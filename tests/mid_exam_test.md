Testing each python file:
1: 
PS D:\8th Semester\Capstone Lab\project> py src/ingest_data.py
Ignoring wrong pointing object 6 0 (offset 0)
Ignoring wrong pointing object 8 0 (offset 0)
Ignoring wrong pointing object 10 0 (offset 0)
Ignoring wrong pointing object 21 0 (offset 0)
Ignoring wrong pointing object 23 0 (offset 0)
Ignoring wrong pointing object 40 0 (offset 0)
Ignoring wrong pointing object 76 0 (offset 0)
Ignoring wrong pointing object 78 0 (offset 0)
Ignoring wrong pointing object 80 0 (offset 0)
Ingested 12 documents.

2nd : 
PS D:\8th Semester\Capstone Lab\project> py src/chunck_and_embed.py
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 12/12 [01:17<00:00,  6.42s/it] 
Embeddings with chunking created.

3rd:
PS D:\8th Semester\Capstone Lab\project> py src/retrieve.py        

---
 NEURALBRAINFIELDS: A NERF-INSPIREDAPPROACH FORGENERATING NONEXISTENTEEG ELECTRODES Shahar Ain Kedem∗ shaharai@post.bgu.ac.il Itamar Zimerman† zimerman1@mail.tau.ac.il Eliya Nachmani∗ eliyanac@bgu.ac.il ABSTRACT Electroencephalography (EEG) data present unique modeling challenges because recordings vary in length, exhibit very low signal to noise ratios, differ signifi- cantly across participants, drift over time within sessions, and are rarely available in large and clean datasets. Consequently,
Metadata: {'doc_type': 'research_paper', 'paper_id': '2601.00012v1', 'field': 'cs', 'source': 'arxiv', 'year': '2024'}

---
 Forking Anatomy: How MorphoDepot Applies the Open-Source Development Model to 3D Digital Morphology A. Murat Maga*, **, Department of Pediatrics, University of Washington, Seattle WA 98195; Center for Developmental Biology and Regenerative Medicine, Seattle Children’s Research Institute, Seattle, WA 
98101; ORCID: 0000-0002-7921-9018 Steve Pieper*, Isomics, Inc., Cambridge, MA 02138; ORCID: 0000-0003-4193-9578 Cassandra Donatelli, Department, School of Engineering and Technology, University of Wa

---
 Draft version January 5, 2026 Typeset using LATEXtwocolumnstyle in AASTeX631 Born in the Dark: The Catastrophic Collapse of F uzzy Dark Matter Solitons as the Origin of Little Red Dots Tak-Pong Woo1, 2 1Institute of Astrophysics, National Taiwan University, Taipei 10617, Taiwan 2Department of Physics, National Taiwan University, Taipei 10617, Taiwan ABSTRACT JWST surveys have uncovered a population of compact, red sources (“Little Red Dots,” LRDs) 
at z≳5 that exhibit broad Balmer emission yet re
Metadata: {'paper_id': '2601.00044v1', 'year': '2024', 'field': 'cs', 'source': 'arxiv', 'doc_type': 'research_paper'}

4th:
PS D:\8th Semester\Capstone Lab\project> py src/tools.py
🧪 Testing tools.py
✅ Loaded 4 tools:
  - query_evidence_base: Query the vector database for evidence related to ...
  - calculate_verification_confidence: Calculate a confidence score for claim verificatio...
  - fetch_paper_metadata: Fetch paper metadata from academic APIs like arXiv...
  - verify_citation_accuracy: Verify the accuracy of a citation by checking iden...


5th:
PS D:\8th Semester\Capstone Lab\project> py src/vector_store.py
Vector DB persisted successfully. Total documents: 2063

6th:
PS D:\8th Semester\Capstone Lab\project> py src/graph.py
INFO:memory:✅ Custom SQLite checkpointer initialized at D:\8th Semester\Capstone Lab\project\src\checkpoints\checkpoints.db
Building Hallucination Detector Graph...
✅ Graph built successfully!

📊 Graph Structure:
  [Start] → Agent → Router → (Tool → Agent) or [End]

7th:
PS D:\8th Semester\Capstone Lab\project> py src/run_agent.py
INFO:graph:✅ Imported 4 tools
INFO:graph:✅ Imported HITL modules
INFO:memory:✅ Using MemorySaver (in-memory checkpointing)
INFO:graph:✅ Imported memory
INFO:graph:Building Hallucination Detector Graph...
INFO:graph:✅ Graph built successfully!
============================================================
🔍 HALLUCINATION DETECTOR AGENT
============================================================
Query: Verify this claim: 'Fine-tuning LLMs reduces hallucinations in medical papers'

INFO:graph:Building Hallucination Detector Graph...
INFO:graph:✅ Graph built successfully!
INFO:graph:🤖 Agent Node: Thinking...
INFO:graph:Available Ollama models: ['llama3.2:1b']
INFO:graph:✅ Connected to Ollama with model: llama3.2:1b
INFO:graph:✅ Tools bound to LLM using bind_tools()
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
INFO:graph:🤖 Agent requested 1 tool calls
INFO:graph:  - Tool: query_evidence_base
INFO:graph:✅ Agent responded (iteration 1)

📝 [agent] AIMessage: }

{
  "name": "calculate_verification_confidence",
  "parameters": {
    "claim": "Fine-tuning LLMs reduces hallucinations in medical papers",
    "evidence_texts": "[{\"source_name\": \"CCS\", \"sou...

============================================================
✅ FINAL RESULT
============================================================

}

{
  "name": "calculate_verification_confidence",
  "parameters": {
    "claim": "Fine-tuning LLMs reduces hallucinations in medical papers",
    "evidence_texts": "[{\"source_name\": \"CCS\", \"source_metadata\": {\"publisher\": \"Elsevier\", \"year\": 2022, \"access_url\": \"https://doi.org/10.1016/j.tclu.2021.09.001\"}}]",
    "evidence_sources": "[\"CCS\"]"
  }
}

{
  "name": "fetch_paper_metadata",
  "parameters": {
    "paper_title": "Fine-tuning LLMs reduces hallucinations in medical papers",
    "arxiv_id": "",
    "doi": ""
  }
}

📊 Summary:
  - Total messages: 2
  - Iterations: 1

8th:
PS D:\8th Semester\Capstone Lab\project> py src/mcp_client.py
INFO:__main__:Connecting to server: D:\8th Semester\Capstone Lab\project\src\mcp_server.py
INFO:__main__:Connected to server. Available tools: ['search_evidence', 'verify_claim']

============================================================
🔍 TEST 1: Search for evidence
============================================================
INFO:__main__:Calling tool: search_evidence with args: {'query': 'Fine-tuning LLMs reduces hallucinations', 'num_results': 2}
Result: {
  "query": "Fine-tuning LLMs reduces hallucinations",
  "evidence": "Error: 'StructuredTool' object is not callable",
  "status": "error"
}

============================================================
✅ TEST 2: Verify a claim
INFO:__main__:Calling tool: verify_claim with args: {'claim': 'Fine-tuning LLMs reduces hallucinations in medical papers'}
Result: {
  "claim": "Fine-tuning LLMs reduces hallucinations in medical papers",
  "verification": "Error: 'StructuredTool' object is not callable",
  "status": "error"
}
INFO:__main__:Disconnected from server
PS D:\8th Semester\Capstone Lab\project> py src/mcp_client.py
INFO:__main__:Connecting to server: D:\8th Semester\Capstone Lab\project\src\mcp_server.py
INFO:__main__:Connected to server. Available tools: ['search_evidence', 'verify_claim', 'fetch_paper', 'verify_citation']

============================================================
🔍 TEST 1: Search for evidence
============================================================
INFO:__main__:Calling tool: search_evidence with args: {'query': 'Fine-tuning LLMs reduces hallucinations', 'num_results': 2}
Result: {
  "status": "success",
  "query": "Fine-tuning LLMs reduces hallucinations",
  "evidence": "\nEvidence 1 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2601.00012v1\nExcerpt: 1\u20135. IEEE, 2025. Christoph M Michel, Micah M Murray, G \u00a8oran Lantz, Sara Gonzalez, Laurent Spinelli, and Rolando Grave De Peralta. Eeg source imaging.Clinical neurophysiology, 115(10):2195\u20132222, 2004. Ben Mildenhall, Pratul P Srinivasan, Matthew Tancik, Jonathan T Barron, Ravi Ramamoorthi, and Ren N...\n\n\nEvidence 2 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2601.00012v1\nExcerpt: d for upsampling or restoring channels.Journal of Neuroscience Methods, 355:109126, 2021b. ISSN 0165-0270. doi: https://doi.org/10. 1016/j.jneumeth.2021.109126. URLhttps://www.sciencedirect.com/science/ article/pii/S0165027021000613. 14 Ke Tan, Buye Xu, Anurag Kumar, Eliya Nachmani, and Yossi Adi. S...\n",
  "num_results": 2
}

============================================================
✅ TEST 2: Verify a claim
============================================================
INFO:__main__:Calling tool: verify_claim with args: {'claim': 'Fine-tuning LLMs reduces hallucinations in medical papers'}
Result: {
  "status": "success",
  "claim": "Fine-tuning LLMs reduces hallucinations in medical papers",
  "evidence": "\nEvidence 1 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2601.00012v1\nExcerpt: 1\u20135. IEEE, 2025. Christoph M Michel, Micah M Murray, G \u00a8oran Lantz, Sara Gonzalez, Laurent Spinelli, and Rolando Grave De Peralta. Eeg source imaging.Clinical neurophysiology, 115(10):2195\u20132222, 2004. Ben Mildenhall, Pratul P Srinivasan, Matthew Tancik, Jonathan T Barron, Ravi Ramamoorthi, and Ren N...\n\n\nEvidence 2 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2601.00012v1\nExcerpt:  65(1):99\u2013106, 2021. Thomas M\u00a8uller, Alex Evans, Christoph Schied, and Alexander Keller. Instant neural graphics prim- itives with a multiresolution hash encoding.ACM transactions on graphics (TOG), 41(4):1\u201315, 2022. Ernst Niedermeyer and FH Lopes da Silva.Electroencephalography: basic principles, c...\n\n\nEvidence 3 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2601.00012v1\nExcerpt: o Yun. Advances, challenges, and prospects of electroencephalography-based biomarkers for psychiatric disorders: a narrative review.Journal of Yeungnam Medical Science, 41(4):261\u2013268, 2024. Tianli Zhao, Jiayuan Chen, Cong Leng, and Jian Cheng. Tinynerf: Towards 100 x compression of voxel radiance fi...\n",
  "verification": {
    "confidence_score": 50,
    "assessment": "WEAKLY SUPPORTED",
    "details": {
      "num_evidence_snippets": 1,
      "unique_sources": 1,
      "avg_evidence_length": 1217.0
    },
    "recommendation": "Limited evidence - consider gathering more sources",
    "timestamp": "2026-03-08T00:12:00.721648"
  },
  "evidence_count": 1
}
INFO:__main__:Disconnected from server

9th:
PS D:\8th Semester\Capstone Lab\project> py src/search.py "Fine-tuning LLMs"
🔍 Searching: Fine-tuning LLMs
INFO:mcp_client:Connecting to server: D:\8th Semester\Capstone Lab\project\src\mcp_server.py
INFO:mcp_client:Connected to server. Available tools: ['search_evidence', 'verify_claim', 'fetch_paper', 'verify_citation']
INFO:mcp_client:Calling tool: search_evidence with args: {'query': 'Fine-tuning LLMs', 'num_results': 3}
Result: {
  "status": "success",
  "query": "Fine-tuning LLMs",
  "evidence": "\nEvidence 1 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2602.17665v1\nExcerpt:  cient multi-GPU distributed training. The model is trained for one epoch with a learning rate of2\u00d710 \u22125, cosine learning rate scheduling, 0.05 warmup ratio, and a batch size of 16. and a batch size of 16. The maximum sequence length is set to 4096 tokens to support long-context conversational tool ...\n\n\nEvidence 2 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2602.17665v1\nExcerpt:  Overall, these results suggest that targeted training with tool schemas and trajectories can outperform larger gen- 14 eral models on geospatial tool-use, especially under strict order/frequency con- straints. Model Param. F1 scores T ool Order Accuracy Per. Op. Logic. GIS. AnyOr. SameO. Uni. Ans. ...\n\n\nEvidence 3 (Confidence: 0.50):\nSource: arxiv | Type: research_paper\nPaper ID: 2601.00012v1\nExcerpt: Borderick Top-1 (\u2191) Top-10 (\u2191) Top-1 (\u2191) Top-10 (\u2191) Top-1 (\u2191) Top-10 (\u2191) Brainmagick (D\u00b4efossez et al., 2023)5.2\u00b10.8 25.7\u00b12.9 41.3\u00b10.1 70.7\u00b10.1 5.0\u00b10.4 17.0\u00b10.6 Transformer-V AE (Chen et al., 2025)4.1 26.82 \u2013 \u2013 \u2013 \u2013 NBF (Our) 9.64\u00b10.33 36.94\u00b10.1 42.1\u00b10.1 71.33\u00b10.1 7.44\u00b10.13 22.68\u00b10.08 Table 2: Perfor...\n",
  "num_results": 3
}

📚 Results:

Evidence 1 (Confidence: 0.50):
Source: arxiv | Type: research_paper
Paper ID: 2602.17665v1
Excerpt:  cient multi-GPU distributed training. The model is trained for one epoch with a learning rate of2×10 −5, cosine learning rate scheduling, 0.05 warmup ratio, and a batch size of 16. and a batch size of 16. The maximum sequence length is set to 4096 tokens to support long-context conversational tool ...


Evidence 2 (Confidence: 0.50):
Source: arxiv | Type: research_paper
Paper ID: 2602.17665v1
Excerpt:  Overall, these results suggest that targeted training with tool schemas and trajectories can outperform larger gen- 14 eral models on geospatial tool-use, especially under strict order/frequency con- straints. Model Param. F1 scores T ool Order Accuracy Per. Op. Logic. GIS. AnyOr. SameO. Uni. Ans. ...


Evidence 3 (Confidence: 0.50):
Source: arxiv | Type: research_paper
Paper ID: 2601.00012v1
Excerpt: Borderick Top-1 (↑) Top-10 (↑) Top-1 (↑) Top-10 (↑) Top-1 (↑) Top-10 (↑) Brainmagick (D´efossez et al., 2023)5.2±0.8 25.7±2.9 41.3±0.1 70.7±0.1 5.0±0.4 17.0±0.6 Transformer-V AE (Chen et al., 2025)4.1 26.82 – – – – NBF (Our) 9.64±0.33 36.94±0.1 42.1±0.1 71.33±0.1 7.44±0.13 22.68±0.08 Table 2: Perfor...

INFO:mcp_client:Disconnected from server

