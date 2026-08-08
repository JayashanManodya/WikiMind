"""Neo4j Graph Database core module providing connections, schema initialization, 
multi-user data isolation, BM25 full-text indexing, and graph traversal operations for WikiMind.
"""

import os
import re
import json
import logging

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver

from .config import get_settings

logger = logging.getLogger("wikimind.graph_db")

_driver_instance: Optional[Driver] = None
_neo4j_available: Optional[bool] = None


def is_neo4j_active() -> bool:
    """Check if Neo4j database connection is active and authenticated."""
    global _driver_instance, _neo4j_available
    if _neo4j_available is not None:
        return _neo4j_available

    settings = get_settings()
    uri = os.getenv("NEO4J_URI", settings.neo4j_uri)
    user = os.getenv("NEO4J_USER", settings.neo4j_user)
    password = os.getenv("NEO4J_PASSWORD", settings.neo4j_password)

    logger.info(f"Connecting to Neo4j Graph DB at: {uri}")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        _driver_instance = driver
        _neo4j_available = True
        logger.info("Successfully connected and verified connectivity with Neo4j!")
    except Exception as e:
        _neo4j_available = False
        _driver_instance = None
        logger.warning(f"Neo4j Graph DB unavailable or authentication failed ({e}). Operating in local filesystem fallback mode.")

    return _neo4j_available


def get_neo4j_driver() -> Optional[Driver]:
    """Get singleton Neo4j driver connection pool if active."""
    if is_neo4j_active():
        return _driver_instance
    return None


def init_neo4j_schema():
    """Initialize Neo4j database schema constraints, indexes, and full-text search indexes."""
    driver = get_neo4j_driver()
    if not driver:
        return

    try:
        logger.info("Initializing Neo4j schema constraints and Lucene BM25 full-text indexes...")
        
        statements = [
            # User constraint
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            
            # WikiPage composite index
            "CREATE INDEX wikipage_user_title_idx IF NOT EXISTS FOR (p:WikiPage) ON (p.user_id, p.title)",
            
            # ChatSession constraint
            "CREATE CONSTRAINT chatsession_id_unique IF NOT EXISTS FOR (s:ChatSession) REQUIRE s.id IS UNIQUE",
            
            # Lucene Full-Text Search Index on WikiPages for BM25 keyword matching
            """
            CREATE FULLTEXT INDEX wiki_fulltext_idx IF NOT EXISTS 
            FOR (n:WikiPage) ON EACH [n.title, n.summary, n.content]
            """
        ]
        
        with driver.session() as session:
            for stmt in statements:
                try:
                    session.run(stmt)
                except Exception as e:
                    logger.warning(f"Neo4j Schema init statement note: {e}")
        
        logger.info("Neo4j schema initialization completed.")
    except Exception as e:
        logger.warning(f"Neo4j init_neo4j_schema note: {e}")


def upsert_user_node(user_id: str, email: str = "", name: str = "", picture: str = "") -> Dict[str, Any]:
    """Create or update User node in Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        return {"id": user_id, "email": email, "name": name}

    try:
        query = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.email = $email, u.name = $name, u.picture = $picture, u.created_at = datetime()
        ON MATCH SET u.email = CASE WHEN $email <> '' THEN $email ELSE u.email END,
                     u.name = CASE WHEN $name <> '' THEN $name ELSE u.name END,
                     u.picture = CASE WHEN $picture <> '' THEN $picture ELSE u.picture END,
                     u.updated_at = datetime()
        RETURN u.id AS id, u.email AS email, u.name AS name, u.picture AS picture
        """
        with driver.session() as session:
            res = session.run(query, user_id=user_id, email=email, name=name, picture=picture)
            record = res.single()
            return record.data() if record else {"id": user_id, "email": email, "name": name}
    except Exception as e:
        logger.warning(f"Neo4j upsert_user_node note: {e}")
        return {"id": user_id, "email": email, "name": name}


def save_wiki_page(
    user_id: str,
    title: str,
    summary: str,
    content: str,
    category: str = "General",
    file_name: str = "",
    linked_titles: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Save a WikiPage node in Neo4j linked to the user, and establish [:LINKED_TO] graph edges."""
    driver = get_neo4j_driver()
    if not driver:
        return {"title": title, "summary": summary}

    try:
        linked_titles = linked_titles or []
        now_str = datetime.now(timezone.utc).isoformat()

        cypher = """
        MERGE (u:User {id: $user_id})
        MERGE (p:WikiPage {user_id: $user_id, title: $title})
        SET p.summary = $summary,
            p.content = $content,
            p.category = $category,
            p.file_name = $file_name,
            p.updated_at = $now_str
        MERGE (u)-[:OWNS]->(p)
        WITH u, p
        FOREACH (target_title IN $linked_titles |
            MERGE (target:WikiPage {user_id: $user_id, title: target_title})
            ON CREATE SET target.summary = 'Auto-referenced concept page connected in Knowledge Graph',
                          target.content = '# ' + target_title + '\n\n**Entity Type**: `CONCEPT`  \n\n## Overview\nAuto-referenced entity concept connected via Knowledge Graph relationships.\n\n## Document Sources\n- [' + $file_name + '](file://' + $file_name + ')',
                          target.category = 'Concept'
            MERGE (u)-[:OWNS]->(target)
            MERGE (p)-[:LINKED_TO {created_at: $now_str}]->(target)
        )

        RETURN p.title AS title, p.summary AS summary, p.category AS category, p.file_name AS file_name
        """

        
        with driver.session() as session:
            res = session.run(
                cypher,
                user_id=user_id,
                title=title,
                summary=summary,
                content=content,
                category=category,
                file_name=file_name,
                linked_titles=linked_titles,
                now_str=now_str
            )
            rec = res.single()
            return rec.data() if rec else {"title": title, "summary": summary}
    except Exception as e:
        logger.warning(f"Neo4j save_wiki_page note: {e}")
        return {"title": title, "summary": summary}


def get_user_wiki_pages(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all WikiPage nodes owned by a specific user."""
    driver = get_neo4j_driver()
    if not driver:
        return []

    try:
        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage)
        OPTIONAL MATCH (p)-[:LINKED_TO]->(target:WikiPage)
        WHERE (u)-[:OWNS]->(target)
        RETURN p.title AS title,
               p.summary AS summary,
               p.content AS content,
               p.category AS category,
               p.file_name AS file_name,
               p.updated_at AS updated_at,
               collect(DISTINCT target.title) AS links
        ORDER BY p.updated_at DESC
        """
        with driver.session() as session:
            res = session.run(cypher, user_id=user_id)
            return [r.data() for r in res]
    except Exception as e:
        logger.warning(f"Neo4j get_user_wiki_pages error: {e}")
        return []


def get_wiki_page_by_title(user_id: str, title: str) -> Optional[Dict[str, Any]]:
    """Get specific WikiPage node content by title for a specific user."""
    driver = get_neo4j_driver()
    if not driver:
        return None

    try:
        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage {title: $title})
        OPTIONAL MATCH (p)-[:LINKED_TO]->(target:WikiPage)
        WHERE (u)-[:OWNS]->(target)
        RETURN p.title AS title,
               p.summary AS summary,
               p.content AS content,
               p.category AS category,
               p.file_name AS file_name,
               p.updated_at AS updated_at,
               collect(DISTINCT target.title) AS links
        """
        with driver.session() as session:
            res = session.run(cypher, user_id=user_id, title=title)
            rec = res.single()
            return rec.data() if rec and rec["title"] else None
    except Exception as e:
        logger.warning(f"Neo4j get_wiki_page_by_title error: {e}")
        return None


def delete_wiki_page(user_id: str, title: str) -> bool:
    """Delete a WikiPage node and its relationships for a specific user."""
    driver = get_neo4j_driver()
    if not driver:
        return False

    try:
        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage {title: $title})
        DETACH DELETE p
        """
        with driver.session() as session:
            session.run(cypher, user_id=user_id, title=title)
            return True
    except Exception as e:
        logger.warning(f"Neo4j delete_wiki_page error: {e}")
        return False


_STOP_WORDS = {
    "what", "is", "a", "an", "the", "who", "where", "how", "tell", "me", "about", 
    "can", "you", "explain", "does", "do", "did", "was", "were", "which", "whose", 
    "why", "in", "on", "at", "for", "with", "of", "and", "or", "to", "from", "by"
}

def search_wiki_graph(user_id: str, search_query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Hybrid keyword-based graph traversal retrieval scoped strictly to user_id."""
    driver = get_neo4j_driver()
    if not driver:
        return []

    # Extract meaningful search keywords from natural language question
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", search_query.lower())
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) >= 2]
    if not keywords:
        keywords = [search_query.lower().strip()]

    try:
        # 1. Match any extracted keyword against node title, summary, or content
        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage)
        WHERE ANY(term IN $keywords WHERE toLower(p.title) CONTAINS term OR toLower(p.summary) CONTAINS term OR toLower(p.content) CONTAINS term)
        WITH u, p LIMIT $limit
        OPTIONAL MATCH (p)-[r:LINKED_TO*0..2]-(connected:WikiPage)
        WHERE (u)-[:OWNS]->(connected)
        RETURN DISTINCT connected.title AS title,
                        connected.summary AS summary,
                        connected.content AS content,
                        connected.category AS category
        LIMIT 8
        """
        with driver.session() as session:
            res = session.run(cypher, user_id=user_id, keywords=keywords, limit=limit)
            results = [r.data() for r in res]
            
        if results:
            return results

        # 2. Fallback: Return top user Wiki pages if no specific keyword matched
        fallback_pages = get_user_wiki_pages(user_id)
        return fallback_pages[:5] if fallback_pages else []
    except Exception as e:
        logger.warning(f"Neo4j search_wiki_graph error: {e}")
        fallback_pages = get_user_wiki_pages(user_id)
        return fallback_pages[:5] if fallback_pages else []



def consolidate_user_knowledge_graph(user_id: str) -> Dict[str, Any]:
    """Clean up and unify user's Neo4j database graph:
    1. Find primary PERSON node (e.g. 'Jayashan Manodya').
    2. Identify duplicate document-stub nodes (matching '* CV', '*_CV', '* Profile', '*.pdf').
    3. Re-route all [:LINKED_TO] relationships from stub nodes directly to the primary PERSON node.
    4. Delete duplicate stub nodes (`DETACH DELETE stub`).
    5. Connect any disconnected sub-graph components directly to the primary PERSON node.
    """
    driver = get_neo4j_driver()
    if not driver:
        return {"consolidated": False}

    try:
        # Step 1: Find primary PERSON node owned by user
        find_primary_cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage)
        WHERE (p.category = 'PERSON' OR p.category = 'Person' OR p.category = 'PERSONS')
              AND NOT p.title ENDS WITH ' Cv' AND NOT p.title ENDS WITH ' CV' AND NOT p.title ENDS WITH '.pdf'
        RETURN p.title AS title
        ORDER BY size(p.content) DESC
        LIMIT 1
        """
        
        with driver.session() as session:
            res = session.run(find_primary_cypher, user_id=user_id)
            rec = res.single()
            primary_title = rec["title"] if rec else None

        if not primary_title:
            # Fallback to largest page if no PERSON category node
            fallback_cypher = """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage)
            WHERE NOT p.title ENDS WITH ' Cv' AND NOT p.title ENDS WITH ' CV' AND NOT p.title ENDS WITH '.pdf'
            RETURN p.title AS title
            ORDER BY size(p.content) DESC
            LIMIT 1
            """
            with driver.session() as session:
                res = session.run(fallback_cypher, user_id=user_id)
                rec = res.single()
                primary_title = rec["title"] if rec else None

        if not primary_title:
            return {"consolidated": False, "reason": "No primary node found"}

        # Step 2: Re-route outgoing links from stub nodes to primary_title
        reroute_out = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(target:WikiPage {title: $primary_title})
        MATCH (u)-[:OWNS]->(stub:WikiPage)
        WHERE stub.title <> $primary_title AND (
            replace(replace(replace(toLower(stub.title), "_", " "), "-", " "), ".", " ") STARTS WITH replace(replace(replace(toLower($primary_title), "_", " "), "-", " "), ".", " ")
            OR stub.category = 'DOCUMENT'
            OR stub.category = 'Document'
            OR stub.title =~ '(?i).*\\\\.[a-z0-9]{2,4}$'
        )
        MATCH (stub)-[:LINKED_TO]->(other:WikiPage)
        WHERE other <> target AND other <> stub
        MERGE (target)-[:LINKED_TO]->(other)
        """
        
        # Step 3: Re-route incoming links to stub nodes
        reroute_in = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(target:WikiPage {title: $primary_title})
        MATCH (u)-[:OWNS]->(stub:WikiPage)
        WHERE stub.title <> $primary_title AND (
            replace(replace(replace(toLower(stub.title), "_", " "), "-", " "), ".", " ") STARTS WITH replace(replace(replace(toLower($primary_title), "_", " "), "-", " "), ".", " ")
            OR stub.category = 'DOCUMENT'
            OR stub.category = 'Document'
            OR stub.title =~ '(?i).*\\\\.[a-z0-9]{2,4}$'
        )
        MATCH (other2:WikiPage)-[:LINKED_TO]->(stub)
        WHERE other2 <> target AND other2 <> stub
        MERGE (other2)-[:LINKED_TO]->(target)
        """

        # Step 4: Detach delete duplicate stub nodes
        delete_stubs = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(target:WikiPage {title: $primary_title})
        MATCH (u)-[:OWNS]->(stub:WikiPage)
        WHERE stub.title <> $primary_title AND (
            replace(replace(replace(toLower(stub.title), "_", " "), "-", " "), ".", " ") STARTS WITH replace(replace(replace(toLower($primary_title), "_", " "), "-", " "), ".", " ")
            OR stub.category = 'DOCUMENT'
            OR stub.category = 'Document'
            OR stub.title =~ '(?i).*\\\\.[a-z0-9]{2,4}$'
        )
        DETACH DELETE stub
        """

        # Step 5: Connect any floating disconnected sub-graph components directly to primary_title
        connect_islands = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(primary:WikiPage {title: $primary_title})
        MATCH (u)-[:OWNS]->(p:WikiPage)
        WHERE p <> primary AND NOT (primary)-[:LINKED_TO*1..3]-(p)
        MERGE (primary)-[:LINKED_TO]->(p)
        """

        with driver.session() as session:
            session.run(reroute_out, user_id=user_id, primary_title=primary_title)
            session.run(reroute_in, user_id=user_id, primary_title=primary_title)
            session.run(delete_stubs, user_id=user_id, primary_title=primary_title)
            session.run(connect_islands, user_id=user_id, primary_title=primary_title)

        logger.info(f"Successfully consolidated knowledge graph for user {user_id} around primary node '{primary_title}'")
        return {"consolidated": True, "primary_title": primary_title}

    except Exception as e:
        logger.warning(f"Neo4j consolidate_user_knowledge_graph error: {e}")
        return {"consolidated": False, "error": str(e)}


def get_user_knowledge_graph(user_id: str) -> Dict[str, Any]:
    """Retrieve full knowledge graph nodes & edges formatted for 2D/3D physics graph UI."""
    driver = get_neo4j_driver()
    if not driver:
        return {"nodes": [], "links": []}

    try:
        # Auto-consolidate graph to merge stub nodes and unite disconnected components
        consolidate_user_knowledge_graph(user_id)

        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:WikiPage)
        OPTIONAL MATCH (p)-[r:LINKED_TO]->(target:WikiPage)
        WHERE target IS NULL OR (u)-[:OWNS]->(target)
        RETURN p.title AS source_title,
               p.category AS source_category,
               p.summary AS source_summary,
               p.file_name AS source_file,
               target.title AS target_title,
               target.category AS target_category,
               target.summary AS target_summary,
               target.file_name AS target_file
        """
        
        nodes_map = {}
        links = []

        with driver.session() as session:
            res = session.run(cypher, user_id=user_id)
            for rec in res:
                src = rec["source_title"]
                if src and src not in nodes_map:
                    nodes_map[src] = {
                        "id": src,
                        "name": src,
                        "label": src,
                        "type": rec["source_category"] or "General",
                        "category": rec["source_category"] or "General",
                        "summary": rec["source_summary"] or "",
                        "filename": rec["source_file"] or "Ingested Document"
                    }
                tgt = rec["target_title"]
                if tgt:
                    if tgt not in nodes_map:
                        nodes_map[tgt] = {
                            "id": tgt,
                            "name": tgt,
                            "label": tgt,
                            "type": rec["target_category"] or "Concept",
                            "category": rec["target_category"] or "Concept",
                            "summary": rec["target_summary"] or "",
                            "filename": rec["target_file"] or "Ingested Document"
                        }
                    links.append({
                        "source": src,
                        "target": tgt,
                        "type": "LINKED_TO"
                    })

        return {
            "nodes": list(nodes_map.values()),
            "links": links,
            "edges": links
        }

    except Exception as e:
        logger.warning(f"Neo4j get_user_knowledge_graph error: {e}")
        return {"nodes": [], "links": []}


# ==========================================
# Chat Session & History Neo4j Management
# ==========================================

def create_chat_session(user_id: str, session_id: str, title: str = "New Chat") -> Dict[str, Any]:
    """Create a new ChatSession node linked to User in Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        return {"id": session_id, "title": title}

    try:
        now_str = datetime.now(timezone.utc).isoformat()
        cypher = """
        MERGE (u:User {id: $user_id})
        MERGE (s:ChatSession {id: $session_id})
        SET s.title = $title, s.user_id = $user_id, s.created_at = $now_str, s.updated_at = $now_str
        MERGE (u)-[:HAS_SESSION]->(s)
        RETURN s.id AS id, s.title AS title, s.created_at AS created_at
        """
        with driver.session() as session:
            res = session.run(cypher, user_id=user_id, session_id=session_id, title=title, now_str=now_str)
            rec = res.single()
            return rec.data() if rec else {"id": session_id, "title": title}
    except Exception as e:
        logger.warning(f"Neo4j create_chat_session error: {e}")
        return {"id": session_id, "title": title}


def save_chat_message(user_id: str, session_id: str, role: str, content: str, citations: str = "[]") -> Dict[str, Any]:
    """Save a ChatMessage node linked to ChatSession in Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        return {"role": role, "content": content}

    try:
        now_str = datetime.now(timezone.utc).isoformat()
        msg_id = f"msg_{datetime.now(timezone.utc).timestamp()}"
        cypher = """
        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:ChatSession {id: $session_id})
        CREATE (m:ChatMessage {id: $msg_id, role: $role, content: $content, citations: $citations, created_at: $now_str})
        CREATE (s)-[:HAS_MESSAGE]->(m)
        SET s.updated_at = $now_str
        RETURN m.id AS id, m.role AS role, m.content AS content, m.citations AS citations, m.created_at AS created_at
        """
        with driver.session() as session:
            res = session.run(
                cypher, user_id=user_id, session_id=session_id, msg_id=msg_id,
                role=role, content=content, citations=citations, now_str=now_str
            )
            rec = res.single()
            return rec.data() if rec else {"role": role, "content": content}
    except Exception as e:
        logger.warning(f"Neo4j save_chat_message error: {e}")
        return {"role": role, "content": content}


def get_chat_history(user_id: str, session_id: str) -> List[Dict[str, Any]]:
    """Retrieve message history for a specific ChatSession."""
    driver = get_neo4j_driver()
    if not driver:
        return []

    try:
        cypher = """
        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:ChatSession {id: $session_id})-[:HAS_MESSAGE]->(m:ChatMessage)
        RETURN m.role AS role, m.content AS content, m.citations AS citations, m.created_at AS created_at
        ORDER BY m.created_at ASC
        """
        with driver.session() as session:
            res = session.run(cypher, user_id=user_id, session_id=session_id)
            return [r.data() for r in res]
    except Exception as e:
        logger.warning(f"Neo4j get_chat_history error: {e}")
        return []


def get_user_chat_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all chat sessions for a user."""
    driver = get_neo4j_driver()
    if not driver:
        return []

    try:
        cypher = """
        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:ChatSession)
        RETURN s.id AS id, s.title AS title, s.created_at AS created_at, s.updated_at AS updated_at
        ORDER BY s.updated_at DESC
        """
        with driver.session() as session:
            res = session.run(cypher, user_id=user_id)
            return [r.data() for r in res]
    except Exception as e:
        logger.warning(f"Neo4j get_user_chat_sessions error: {e}")
        return []


def delete_chat_session(user_id: str, session_id: str) -> bool:
    """Delete a chat session and its message nodes."""
    driver = get_neo4j_driver()
    if not driver:
        return False

    try:
        cypher = """
        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:ChatSession {id: $session_id})
        OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:ChatMessage)
        DETACH DELETE s, m
        """
        with driver.session() as session:
            session.run(cypher, user_id=user_id, session_id=session_id)
            return True
    except Exception as e:
        logger.warning(f"Neo4j delete_chat_session error: {e}")
        return False


