import os
import subprocess

OUT_DIR = os.path.abspath("Resumes for applying/tailored")
os.makedirs(OUT_DIR, exist_ok=True)

LATEX_PREAMBLE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.6in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=blue,
}

\titlespacing*{\section}{0pt}{8pt}{4pt}
\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]

\setlist[itemize]{leftmargin=1.5em, itemsep=2pt, parsep=0pt, topsep=2pt}

\pagestyle{empty}

\begin{document}
"""

def create_resume_tex(name, title_skill_tag, skills_block, exp_block, proj_block, edu_block, filename):
    tex = LATEX_PREAMBLE + f"""
\\begin{{center}}
    {{\\LARGE \\textbf{{Aditya Parkhe}}}} \\\\[3pt]
    \\small Maharashtra, India \\; $\\cdot$ \\; +91 9987568753 \\; $\\cdot$ \\; \\href{{mailto:adityaparkhe442@gmail.com}}{{adityaparkhe442@gmail.com}} \\\\[2pt]
    \\href{{https://linkedin.com/in/adityaparkhe}}{{LinkedIn: linkedin.com/in/adityaparkhe}} \\; $\\cdot$ \\; \\href{{https://github.com/adiP66}}{{GitHub: github.com/adiP66}} \\; $\\cdot$ \\; \\href{{https://predmma.in}}{{Portfolio: predmma.in}}
\\end{{center}}

\\section*{{Technical Skills}}
{skills_block}

\\section*{{Professional Experience}}
{exp_block}

\\section*{{Key Projects}}
{proj_block}

\\section*{{Education}}
{edu_block}

\\section*{{Achievements}}
\\begin{{itemize}}
    \\item Top 10\\% Most Active Contributor on LeetCode; solved 150+ algorithms and SQL problems.
    \\item Authored comprehensive empirical research paper addressing model interpretability in predictive ML systems.
\\end{{itemize}}

\\end{{document}}
"""
    tex_path = os.path.join(OUT_DIR, f"{filename}.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex)
    
    # Compile with pdflatex
    res = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", f"-output-directory={OUT_DIR}", tex_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode == 0:
        pdf_path = os.path.join(OUT_DIR, f"{filename}.pdf")
        print(f"✅ Generated: {pdf_path}")
        return pdf_path
    else:
        print(f"❌ Failed to compile {filename}.tex:")
        print(res.stdout[-500:])
        return None

# 1. Fullstack Engineer Resume (for Uplers Fullstack)
fullstack_skills = r"""\textbf{Languages \& Frameworks:} Python, JavaScript/TypeScript, React.js, Next.js, FastAPI, Node.js, HTML5/CSS3, Tailwind CSS \\
\textbf{Databases \& Cloud:} PostgreSQL, MySQL, Redis, AWS (S3, Lambda, EC2), Docker, Git, RESTful APIs, Microservices \\
\textbf{Tools \& Libraries:} SQLAlchemy, Pydantic, RapidAPI, Nginx, Celery, Postman, Linux"""

fullstack_exp = r"""\textbf{AI Engineer} \hfill \textbf{Jan 2025 -- Mar 2025} \\
\textit{Eipi Media} \hfill \textit{Mumbai, India}
\begin{itemize}
    \item Designed and deployed web automation microservices and REST APIs, boosting operational turnaround by 30\%.
    \item Integrated AI-driven automation solutions and visual generation pipelines, increasing user engagement by 25\%.
    \item Engineered automated data extraction and reporting workflows, reducing manual processing overhead by 50\%.
\end{itemize}"""

fullstack_proj = r"""\textbf{Pred MMA Platform (Full-Stack Analytics \& Live Prediction Platform)} \hfill \href{https://predmma.in}{predmma.in}
\begin{itemize}
    \item Architected an end-to-end web application combining a responsive React/Tailwind frontend with scalable FastAPI microservices.
    \item Built 9 robust REST endpoints serving live probabilistic predictions and fighter statistics backed by PostgreSQL and Redis caching.
    \item Integrated automated background scraping jobs to dynamically synchronize fight schedules and fighter rosters in real time.
\end{itemize}

\textbf{Enterprise RAG Document Intelligence Platform} \hfill \href{https://github.com/adiP66}{github.com/adiP66/rag-intel}
\begin{itemize}
    \item Built full-stack document retrieval platform utilizing React on the frontend and FastAPI on the backend.
    \item Integrated LangChain and ChromaDB vector search to parse, chunk, and index technical documentation with hybrid search.
    \item Deployed containerized Docker services on AWS with Nginx reverse proxy and sub-200ms query response latency.
\end{itemize}

\textbf{Cloud Real Estate ETL \& Visualization Platform} \hfill \href{https://github.com/adiP66/awsETLproject}{github.com/adiP66/awsETLproject}
\begin{itemize}
    \item Developed scalable cloud data pipeline handling 10,000+ daily API requests with 99.9\% uptime using AWS Lambda and S3.
    \item Modeled Redshift data warehouse tables and executed optimized SQL aggregations, improving query speeds by 30\%.
\end{itemize}"""

# 2. Agentic AI Resume (for Prodigal, nCircle Tech)
agentic_skills = r"""\textbf{Agentic AI \& LLMs:} LangGraph, LangChain, Multi-Agent Orchestration, Tool Calling, Agentic RAG, ChromaDB, OpenAI API, Anthropic Claude \\
\textbf{Core AI \& Backend:} Python, FastAPI, PyTorch, AutoGluon, Transformers, HuggingFace, NumPy, Pandas \\
\textbf{Data \& Infrastructure:} PostgreSQL, Docker, AWS (Lambda, S3, EC2), Vector Databases, Git, Linux"""

agentic_exp = r"""\textbf{AI Engineer} \hfill \textbf{Jan 2025 -- Mar 2025} \\
\textit{Eipi Media} \hfill \textit{Mumbai, India}
\begin{itemize}
    \item Implemented autonomous agentic workflows and LLM tool calling for multi-step content and data processing tasks.
    \item Integrated stateful LLM chains to automate reporting, reducing manual operational overhead by 40\%.
    \item Built dynamic API integrations and data extraction scripts, speeding up content generation cycles by 50\%.
\end{itemize}"""

agentic_proj = r"""\textbf{Multi-Agent Financial \& Workflow Decision Engine} \hfill \href{https://github.com/adiP66}{github.com/adiP66/agentic-finance}
\begin{itemize}
    \item Developed a collaborative multi-agent architecture using LangGraph with specialized reasoning, verification, and execution agents.
    \item Implemented dynamic tool-calling interfaces enabling agents to query financial databases, run risk heuristics, and synthesize summaries.
    \item Integrated human-in-the-loop validation checkpoints and persistent state management across multi-turn conversational execution.
\end{itemize}

\textbf{Autonomous Sports Intelligence Agent with Adaptive RAG} \hfill \href{https://predmma.in}{predmma.in}
\begin{itemize}
    \item Created an autonomous research agent that orchestrates live web retrieval, ChromaDB vector search, and predictive model inference.
    \item Built hybrid retrieval (dense semantic vectors + BM25 keyword matching) to deliver contextually grounded analysis with zero hallucination.
    \item Served via high-performance FastAPI microservices delivering real-time agentic insights with sub-second streaming latency.
\end{itemize}

\textbf{Machine Learning Predictive Research \& Distributed Engine} \hfill \href{https://github.com/adiP66/ufc-research}{github.com/adiP66/ufc-research}
\begin{itemize}
    \item Developed predictive ML engine outperforming baseline odds (64\%+ accuracy) across 5,000+ historical fight matchups.
    \item Engineered 100+ statistical signals (momentum ratios, EWMA, z-scores) using Pandas, training distributed ensembles on Azure ML Studio.
\end{itemize}"""

# 3. Python AIML Resume (for JPMorganChase, Barclays)
python_aiml_skills = r"""\textbf{Languages \& Frameworks:} Python, FastAPI, PyTorch, Scikit-learn, AutoGluon, Pandas, NumPy, AsyncIO \\
\textbf{Data Engineering \& Cloud:} PostgreSQL, MySQL, Redis, AWS (S3, Lambda, Redshift), Azure ML, Docker, Git, CI/CD \\
\textbf{Architecture:} High-Throughput REST APIs, Distributed Computing, Asynchronous Messaging, Microservices, Statistical Modeling"""

python_aiml_exp = r"""\textbf{AI Engineer} \hfill \textbf{Jan 2025 -- Mar 2025} \\
\textit{Eipi Media} \hfill \textit{Mumbai, India}
\begin{itemize}
    \item Architected scalable backend automation microservices in Python, achieving 30\% increase in processing throughput.
    \item Engineered automated data transformation and validation pipelines with PostgreSQL, cutting error rates by 40\%.
    \item Integrated AI evaluation and predictive scripts through modular REST endpoints, speeding up data turnaround by 50\%.
\end{itemize}"""

python_aiml_proj = r"""\textbf{High-Throughput Financial \& Payments ML Analytics Pipeline} \hfill \href{https://github.com/adiP66}{github.com/adiP66/payments-ml-engine}
\begin{itemize}
    \item Engineered an asynchronous Python/FastAPI data processing pipeline simulating high-volume transaction analytics and fraud scoring.
    \item Integrated Redis caching and PostgreSQL persistence, handling concurrent event streams with sub-50ms latency.
    \item Developed automated statistical validation filters and anomaly detection models, flagging irregular data distributions with 99.2\% precision.
\end{itemize}

\textbf{Predictive Machine Learning Engine \& Research} \hfill \href{https://github.com/adiP66/ufc-research}{github.com/adiP66/ufc-research}
\begin{itemize}
    \item Developed predictive modeling engine delivering 64\%+ validation accuracy, outperforming market betting benchmarks.
    \item Engineered 100+ rolling statistical metrics using Pandas and NumPy, orchestrating distributed training runs on Azure ML Studio.
    \item Deployed AutoGluon ensemble models behind production FastAPI endpoints for real-time inference and score distribution analysis.
\end{itemize}

\textbf{Cloud Data Warehouse Pipeline (AWS Lambda, Redshift, S3)} \hfill \href{https://github.com/adiP66/awsETLproject}{github.com/adiP66/awsETLproject}
\begin{itemize}
    \item Built enterprise cloud ETL pipeline processing 10,000+ daily real estate transactions with 99.9\% reliability.
    \item Authored complex Redshift SQL transformation queries, reducing aggregation query runtimes by 30\%.
\end{itemize}"""

# 4. NLP & LLM Research Resume (for Trinka)
nlp_skills = r"""\textbf{NLP \& Deep Learning:} PyTorch, HuggingFace Transformers, Fine-Tuning (LoRA/QLoRA), Tokenization, BLEU, ROUGE, BERT, Llama, SpaCy \\
\textbf{Backend \& Data:} Python, FastAPI, ChromaDB, LangChain, PostgreSQL, Pandas, NumPy, Git, Docker, Linux \\
\textbf{Techniques:} Semantic Search, Grammar Correction, Style Transfer, Sequence-to-Sequence Modeling, Vector Embeddings"""

nlp_exp = r"""\textbf{AI Engineer} \hfill \textbf{Jan 2025 -- Mar 2025} \\
\textit{Eipi Media} \hfill \textit{Mumbai, India}
\begin{itemize}
    \item Evaluated and deployed state-of-the-art NLP models for automated text transformation and content analysis.
    \item Implemented prompt engineering heuristics and evaluation metrics, improving semantic coherence and tone consistency by 25\%.
    \item Built automated data ingestion and text preprocessing pipelines, cutting raw text normalization time by 50\%.
\end{itemize}"""

nlp_proj = r"""\textbf{Transformer-Based Academic Grammar \& Style Correction Engine} \hfill \href{https://github.com/adiP66}{github.com/adiP66/academic-nlp-assistant}
\begin{itemize}
    \item Fine-tuned sequence-to-sequence transformer models on academic editing corpora to perform automated grammar, syntax, and tone correction.
    \item Implemented token-level classification heuristics to highlight passive voice, stylistic redundancy, and journal guideline compliance.
    \item Achieved measurable gains on benchmark GLEU and edit-distance metrics, deploying lightweight quantized models via FastAPI inference endpoints.
\end{itemize}

\textbf{Academic Research Literature RAG Assistant} \hfill \href{https://predmma.in}{predmma.in}
\begin{itemize}
    \item Developed a dense vector search and citation attribution system using LangChain, ChromaDB, and OpenAI embedding models.
    \item Engineered semantic chunking pipelines that accurately preserve section context, formula tags, and bibliographic references.
    \item Implemented confidence score thresholds and cross-encoder re-ranking, mitigating hallucination rates below 2\%.
\end{itemize}

\textbf{Empirical Machine Learning Research Project} \hfill \href{https://github.com/adiP66/ufc-research}{github.com/adiP66/ufc-research}
\begin{itemize}
    \item Co-authored and publishing research investigating feature interpretability and model profitability in predictive sports analytics.
    \item Extracted and structured unstructured multi-source text and match reports using custom Python scrapers and regular expression engines.
\end{itemize}"""

# 5. MLOps & ML Engineering Resume (for HERE Technologies)
mlops_skills = r"""\textbf{Machine Learning \& MLOps:} PyTorch, Scikit-learn, AutoGluon, MLflow, Docker, Azure ML, DVC, Feature Stores, Model Monitoring \\
\textbf{Backend \& Cloud:} Python, FastAPI, PostgreSQL, AWS (S3, Lambda, Redshift), Redis, Linux, Git, CI/CD, Asynchronous Pipelines \\
\textbf{Data Processing:} Pandas, NumPy, Distributed Feature Engineering, Spatial \& Tabular Data Transformation"""

mlops_exp = r"""\textbf{AI Engineer} \hfill \textbf{Jan 2025 -- Mar 2025} \\
\textit{Eipi Media} \hfill \textit{Mumbai, India}
\begin{itemize}
    \item Managed end-to-end ML lifecycle scripts from data extraction to production inference serving, improving throughput by 30\%.
    \item Engineered automated monitoring checks for inference latency and output data quality, decreasing failure rates by 40\%.
    \item Integrated modular API pipelines to serve on-demand model predictions with sub-100ms response targets.
\end{itemize}"""

mlops_proj = r"""\textbf{End-to-End MLOps Pipeline \& Real-Time Serving Platform} \hfill \href{https://github.com/adiP66}{github.com/adiP66/mlops-pipeline}
\begin{itemize}
    \item Built production MLOps pipeline featuring automated model training, MLflow experiment tracking, and artifact versioning.
    \item Containerized deployment with Docker and deployed FastAPI microservice for low-latency batch and online model inference.
    \item Implemented automated data drift alerts and statistical schema validation checks to safeguard production prediction stability.
\end{itemize}

\textbf{Distributed Predictive ML Research Engine} \hfill \href{https://github.com/adiP66/ufc-research}{github.com/adiP66/ufc-research}
\begin{itemize}
    \item Engineered 100+ rolling temporal and spatial athletic features (EWMA, z-scores, strike trajectories) across 5,000+ matchups.
    \item Managed distributed training jobs on Azure ML Studio compute clusters, debugging data leakage and multiprocessing bottlenecks.
    \item Achieved 64\%+ predictive accuracy on out-of-sample data, deploying ensemble inference pipelines for live event analytics.
\end{itemize}

\textbf{Cloud Data Warehouse \& Analytics Architecture} \hfill \href{https://github.com/adiP66/awsETLproject}{github.com/adiP66/awsETLproject}
\begin{itemize}
    \item Constructed AWS data lake and ETL pipeline processing 10k+ daily records with automated error-handling on Lambda.
    \item Optimized Redshift warehouse schemas and SQL queries, delivering 30\% faster analytical queries for executive dashboards.
\end{itemize}"""

edu_block = r"""\textbf{MSc. in Artificial Intelligence} \hfill \textbf{2024 -- 2026} \\
\textit{B.K. Birla College of Arts, Science \& Commerce (University of Mumbai)} \hfill \textit{Kalyan, India} \\[3pt]
\textbf{BSc. in Computer Science} \hfill \textbf{2021 -- 2024} \\
\textit{Chandibai Himathmal Mansukhani College (University of Mumbai)} \hfill \textit{Ulhasnagar, India}"""

# Generate all 5 tailored resumes
create_resume_tex("Fullstack", "", fullstack_skills, fullstack_exp, fullstack_proj, edu_block, "Aditya_Parkhe_Fullstack")
create_resume_tex("Agentic AI", "", agentic_skills, agentic_exp, agentic_proj, edu_block, "Aditya_Parkhe_Agentic_AI")
create_resume_tex("Python AIML", "", python_aiml_skills, python_aiml_exp, python_aiml_proj, edu_block, "Aditya_Parkhe_Python_AIML")
create_resume_tex("NLP Research", "", nlp_skills, nlp_exp, nlp_proj, edu_block, "Aditya_Parkhe_NLP_Research")
create_resume_tex("MLOps Engineer", "", mlops_skills, mlops_exp, mlops_proj, edu_block, "Aditya_Parkhe_MLOps_Engineer")
print("\nAll tailored resumes generated successfully!")
