[![Python Application Test with Github Actions](https://github.com/BobZhang26/AIPI-590---XAI-Final-Project/actions/workflows/cicd.yml/badge.svg)](https://github.com/BobZhang26/AIPI-590---XAI-Final-Project/actions/workflows/cicd.yml)
# **XAI: Knowledge Graph Visualization of GraphRAG Model**
## **Introduction**
The demand for transparency and trust in decision-making processes has become
paramount. This is particularly critical in high-stakes domains such as **healthcare** and
**critical care**, where AI-driven decisions directly impact patient outcomes. Recent AI
models such as **GraphRAG** integrate powerful neural network architectures like
transformers with graph-based retrieval and reasoning mechanisms. But the lack of
inherent explainability raises concerns about how physicians and healthcare
professionals can interpret its decisions.

> This project aims to bridge this gap by enhancing the explainability of GraphRAG through the implementation of a visualization method that allows users to explore the underlying knowledge graph. By enabling interaction with the graph's entities and relationships, this approach provides insight into the model's retrieval mechanisms, fostering greater transparency and trust in its decision-making process.

## **Methodology**
This project demonstrates the construction of GraphRAG from scratch, integrating a graph database powered by **Neo4j** and comparing model-generated answers with ground truth data. The methodology involves building the knowledge graph, implementing the retrieval mechanism, and evaluating the model's performance. The process utilizes **LangChain**, **LLM models (Llama 3.1 and GPT-4 Turbo)**, and **OpenAI’s text-embedding-3-large** for entity extraction and retrieval.
<img width="871" alt="Screenshot 2024-12-04 at 23 42 10" src="https://github.com/user-attachments/assets/afba6c91-ca54-48bc-84be-b863e57dc6b2">


---

### **1. Building GraphRAG and Database Integration**

- **Knowledge Graph Construction**:
  - The knowledge graph is constructed using the **LangChain framework**, which facilitates the integration of large language models (LLMs) for entity and relationship extraction.
  - **LLM Models**:
    - **Llama 3.1** and **GPT-4 Turbo** are employed to extract entities and relationships from input text, enabling the creation of a robust graph structure.

- **Database Configuration**:
  - The extracted entities and relationships are stored in a **Neo4j graph database**.
  - Neo4j can be deployed:
    - **Using Docker**: Recommended for users who do not have Neo4j pre-installed on their desktop.
    - **On Desktop**: For users with a local Neo4j setup.
  - The graph database utilizes **Cypher query language**, similar to SQL in relational databases, to manage and retrieve data.

---
### **2. Enhancing Retrieval with Vector Indexing**

- **Vectorization of Entities and Queries**:
  - OpenAI’s **text-embedding-3-large** model is used to vectorize:
    - Input queries.
    - Extracted entities from the knowledge graph.
  - This enables the construction of a **vector index** to enhance retrieval efficiency.

- **Hybrid Retrieval Mechanism**:
  - Combines graph-based retrieval using Cypher queries with vector similarity search to provide accurate and contextually relevant results.

---

### **3. Workflow Implementation**

- **LangChain Workflow**:
  - LangChain orchestrates the entity extraction, knowledge graph construction, and retrieval mechanism, seamlessly integrating LLMs and the Neo4j database.

- **Model Querying and Evaluation**:
  - Input queries are processed through GraphRAG, and the model retrieves information using the hybrid mechanism.
  - The model-generated answers are compared to ground truth data to evaluate accuracy and reliability.

---

### **4. Tools and Frameworks**

- **LangChain**: Provides the framework for knowledge graph creation and integration with LLMs.
- **LLMs**:
  - **Llama 3.1** and **GPT-4 Turbo** for entity and relationship extraction.
- **Neo4j**: Graph database used for storing and querying structured relationships.
  - Deployed via Docker container for accessibility.
- **OpenAI text-embedding-3-large**: Used for vectorizing entities and input queries to build the vector index.

---

### **5. Neo4j Setup and Queries**

- **Deployment Options**:
  - **Docker Container**: Recommended due to ease of setup and portability.
  - **Desktop**: For advanced users with Neo4j pre-installed.
- **Cypher Query Language**:
  - The inherent query language of Neo4j, used to interact with the graph database and retrieve nodes and relationships efficiently.

