"""LangChain RAG pipeline wrapping the existing CaRMS search service."""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_classic.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from sqlmodel import Session

from carms.db.engine import engine
from carms.search.retriever import SearchService

CARMS_RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an expert advisor on Canadian medical residency programs (CaRMS).
Use the following context from program descriptions to answer the question.
If you cannot answer from the provided context, say so honestly.

Context:
{context}

Question: {question}

Answer:""",
)


class CaRMSRetriever(BaseRetriever):
    """Custom LangChain retriever wrapping the existing SearchService.

    Delegates to ``SearchService.search()`` so we reuse the pgvector
    infrastructure without data duplication.
    """

    top_k: int = Field(default=8)

    def _get_relevant_documents(self, query: str, **kwargs: Any) -> list[Document]:
        with Session(engine) as session:
            service = SearchService(session)
            results = service.search(query=query, top_k=self.top_k)

        return [
            Document(
                page_content=r.chunk_text,
                metadata={
                    "program_id": r.program_id,
                    "program_name": r.program_name,
                    "discipline": r.discipline,
                    "school": r.school,
                    "site": r.site,
                    "similarity": r.similarity,
                },
            )
            for r in results
        ]


def create_rag_chain(k: int = 8) -> RetrievalQA:
    """Build a RetrievalQA chain using CaRMS data and Claude as the LLM."""
    retriever = CaRMSRetriever(top_k=k)
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1024)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": CARMS_RAG_PROMPT},
    )
    return chain


def ask(question: str, k: int = 8) -> dict:
    """High-level helper: ask a question and get answer + sources."""
    chain = create_rag_chain(k=k)
    result = chain.invoke({"query": question})

    sources = []
    for doc in result.get("source_documents", []):
        sources.append(
            {
                "program_name": doc.metadata.get("program_name"),
                "discipline": doc.metadata.get("discipline"),
                "school": doc.metadata.get("school"),
                "site": doc.metadata.get("site"),
                "similarity": doc.metadata.get("similarity"),
                "excerpt": doc.page_content[:200],
            }
        )

    return {
        "answer": result["result"],
        "sources": sources,
    }
