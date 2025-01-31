"""This is a library module for graph RAG which will contain helper 
functions for the graph RAG module."""

from sentence_transformers import SentenceTransformer
import ollama
import os
import ast
import pandas as pd
import numpy as np


def embed_entity(entity):
    """
    This function utilizes sentence transformers (default for Neo4j builder)
    to embed a string and return a list of floats

    Args:
        entity: str, entity to embed

    Returns:
        embeddings: list, list of floats
    """
    embeddings = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return embeddings.encode(entity).tolist()


def create_vector_index(graph, name):
    """
    This function creates a vector index in our Neo4j graph Database so that
    we can perform a similarity search on the embeddings of the nodes.

    Args:
      graph: Neo4jGraph object
      name: str, name of the index

    Returns:
      None
    """
    graph.query(f"DROP INDEX `{name}` IF EXISTS")
    graph.query(
        f"""
    CREATE VECTOR INDEX `{name}`
    FOR (a:__Entity__) ON (a.embedding)
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """
    )


def vector_search(graph, query_embedding, index_name="entities", k=5):
    """
    This function performs a similarity search in our Neo4j graph database

    Args:
      graph: Neo4jGraph object
      query_embedding: list, embedding of the query
      index_name: str, name of the index
      k: int, number of results to return

    Returns:
      result: list, list of tuples containing the node id and the similarity score
    """
    similarity_query = f"""
    MATCH (n:`__Entity__`)
    CALL db.index.vector.queryNodes('{index_name}', {k}, {query_embedding})
    YIELD node, score
    RETURN DISTINCT node.id, score
    ORDER BY score DESC
    LIMIT {k}

    """
    result = graph.query(similarity_query)
    return result


def chunk_finder(graph, query):

    # get the id of the query associated node
    query_embedding = embed_entity(query)
    response = vector_search(graph, query_embedding)
    id = response[0]["node.id"]

    chunk_find_query = f"""
    MATCH (n:Chunk)-[r]->(m:`__Entity__` {{id: "{id}"}}) RETURN n.text,n.fileName LIMIT 8
    """
    result = graph.query(chunk_find_query)
    output = []
    for record in result:
        output.append((record["n.fileName"], record["n.text"]))
    return output


def get_entities(prompt, correction_context=" "):

    prompt = f"""
    You are a highly capable natural language processing assistant with extensive medical knowledge. 
    Your task is to extract medical entities from a given prompt. 
    Entities are specific names, places, dates, times, objects, organizations, or other identifiable items explicitly mentioned in the text.
    Please output the entities as a list of strings in the format ["string 1", "string 2"]. Do not include duplicates. 
    Do not include any other text. Always include at least one entity.

    {correction_context}

    Here is the input prompt:
    {prompt}

    Extracted entities: 
    """
    # use generate because we are not chatting with this instance of 3.2
    output = ollama.generate(model="llama3.1:latest", prompt=prompt)
    response = output.response

    # add some error handling to get a list of strings (recursively call the extractor with added context)
    try:
        response = ast.literal_eval(response)
        if not isinstance(response, list):
            correction_string = f"The previous output threw this error: Expected a list of strings, but got {type(response)} with value {response}"
            response = get_entities(prompt, correction_context=correction_string)
    except (ValueError, SyntaxError) as e:
        print(f"Error converting to list: {e}")
        response = get_entities(prompt)

    return response, correction_context


def graph_retriever(graph, query):
    entities, _ = get_entities(query)
    ids = []
    for entity in entities:
        embedding = embed_entity(entity)
        closest_node = vector_search(graph, embedding, k=1)
        id = closest_node[0]["node.id"]
        ids.append(id)
    context = ""
    for id in ids:
        neighbors_query = f"""
        MATCH path = (n:`__Entity__` {{id:"{id}"}})-[r*..2]-(m:`__Entity__`)
        WHERE ALL(rel IN relationships(path) WHERE NOT type(rel) IN ['HAS_ENTITY', 'MENTIONS'])
        RETURN 
        n.id AS startNode,
        [rel IN relationships(path) | 
            {{
            type: type(rel),
            direction: CASE 
                WHEN startNode(rel) = n THEN "outgoing" 
                WHEN endNode(rel) = n THEN "incoming" 
                ELSE "undirected"
            END
            }}] AS relationshipDetails,
        [node IN nodes(path) | node.id] AS pathNodes
        """
        result = graph.query(neighbors_query)
        for record in result:
            rel = record["relationshipDetails"]
            pathNodes = record["pathNodes"]
            formatted_path = ""
            for i in range(len(rel)):
                if rel[i]["direction"] == "outgoing":
                    formatted_path += (
                        f" {pathNodes[i]} {rel[i]['type']} {pathNodes[i+1]},"
                    )
                elif rel[i]["direction"] == "incoming":
                    formatted_path += (
                        f" {pathNodes[i+1]} {rel[i]['type']} {pathNodes[i]},"
                    )
                else:
                    formatted_path += (
                        f" {pathNodes[i]} {rel[i]['type']} {pathNodes[i+1]},"
                    )
            context += formatted_path + "\n"

    return context


def context_builder(graph, query, method="hybrid"):
    """
    This function performs vector search, graph search, or both to build a context string for
    an LLM

    Args:
    graph: Neo4jGraph object
    query: string

    Returns:
    context: string
    """
    context = ""
    if method == "vector":
        output = chunk_finder(graph, query)
        context = "Given the following context in the format [(File Name, Text),...] \n"
        context += str(output)

    elif method == "graph":
        context = graph_retriever(graph, query)
    elif method == "hybrid":

        context = (
            graph_retriever(graph, query)
            + "\n And Given the following context in the format [(File Name, Text),...] \n"
            + str(chunk_finder(graph, query))
        )
    else:
        pass  # no context
    return context


def generate_response(graph, query, method="hybrid", model="llama3.1:latest"):
    """
    This function will utilizze ollama to generate a response while providing context

    Args:
    graph: Neo4jGraph object
    query: string
    method: string, "vector", "graph", or "hybrid"
    model: string, model name

    Returns:
    response: string, generated response
    prompt: string, generated prompt (with context)

    """
    context = context_builder(graph, query, method)
    prompt = f""" 
    You are a highly capable natural language processing assistant with extensive medical knowledge.
    Answer the following question based on the provided context:
    Question: {query}
    Context: {context}
    """

    response = ollama.generate(model=model, prompt=prompt)
    return response, prompt


def run_trial(graph, question_list, num_trials=1):
    """
    This function will run a trial of questions and return the results

    Args:
    graph: Neo4jGraph object
    question_list: list, list of questions

    Returns:
    results: a dataframe where each row is a question and each column is a model mode combination.
    The value will be a list of response strings.
    """
    models = ["llama3.1:latest", "granite3-dense:2b"]
    methods = ["None", "vector", "graph", "hybrid"]

    # we will iterate for each model and method we will generate num_trial answers to each
    # question and store the resulting list of strings in a dataframe

    data = {f"{model}-{method}": [] for model in models for method in methods}

    # Iterate through questions
    for question in question_list:
        for model in models:
            for method in methods:
                responses = []
                for _ in range(num_trials):
                    # Generate a response for the current model, method, and question
                    response, _ = generate_response(
                        graph, question, method=method, model=model
                    )
                    responses.append(response.response)
                # Add the responses to the correct column
                data[f"{model}-{method}"].append(responses)

    # Create a DataFrame where rows are questions
    results = pd.DataFrame(
        data, index=[f"Question {i+1}" for i in range(len(question_list))]
    )
    return results


def create_md(csv_path, output_path, questions):
    """
    This function will convert a trial csv into md for evaluation

    Args:
    csv_path: string, path to the csv file
    output_path: string, path to the output file
    qusetions: list, list of questions

    Returns:
    None
    """
    # Load the CSV file
    df = pd.read_csv(csv_path)

    # Initialize a list to store the markdown content
    markdown_content = []

    # Iterate through each question
    for i in range(len(df)):
        question_number = f"Question {i + 1}"
        markdown_content.append(f"## {question_number} {questions[i]}\n")

        # Iterate through each column (model-method pair)
        for column in df.columns:
            response = df.iloc[i][column]
            markdown_content.append(f"**{column}**:\n\n{response}\n\n")

    # Write the markdown content to a file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_content))
