import React, { createContext, useContext, useState, useCallback } from 'react';
import { getWikiIndex, getWikiGraph, getChatSessions } from '../api/client';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [wikiPages, setWikiPages] = useState(null);
  const [wikiGraph, setWikiGraph] = useState(null);
  const [chatSessions, setChatSessions] = useState(null);

  const [isLoadingWiki, setIsLoadingWiki] = useState(false);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Fetch or return cached Wiki Pages
  const loadWikiPages = useCallback(async (force = false) => {
    if (!force && wikiPages !== null) {
      return wikiPages;
    }
    setIsLoadingWiki(true);
    try {
      const res = await getWikiIndex();
      const pages = res.pages || [];
      setWikiPages(pages);
      return pages;
    } catch (err) {
      console.error("Failed to fetch Wiki Index:", err);
      return wikiPages || [];
    } finally {
      setIsLoadingWiki(false);
    }
  }, [wikiPages]);

  // Fetch or return cached Wiki Graph
  const loadWikiGraph = useCallback(async (force = false) => {
    if (!force && wikiGraph !== null) {
      return wikiGraph;
    }
    setIsLoadingGraph(true);
    try {
      const res = await getWikiGraph();
      const graphData = { nodes: res.nodes || [], edges: res.edges || [] };
      setWikiGraph(graphData);
      return graphData;
    } catch (err) {
      console.error("Failed to fetch Wiki Graph:", err);
      return wikiGraph || { nodes: [], edges: [] };
    } finally {
      setIsLoadingGraph(false);
    }
  }, [wikiGraph]);

  // Fetch or return cached Chat Sessions
  const loadChatSessions = useCallback(async (force = false) => {
    if (!force && chatSessions !== null) {
      return chatSessions;
    }
    setIsLoadingChat(true);
    try {
      const res = await getChatSessions();
      const sessions = res.sessions || [];
      setChatSessions(sessions);
      return sessions;
    } catch (err) {
      console.error("Failed to fetch Chat Sessions:", err);
      return chatSessions || [];
    } finally {
      setIsLoadingChat(false);
    }
  }, [chatSessions]);

  // Invalidate all cached data on new document upload
  const invalidateAll = useCallback(() => {
    setWikiPages(null);
    setWikiGraph(null);
    setChatSessions(null);
  }, []);

  return (
    <DataContext.Provider
      value={{
        wikiPages: wikiPages || [],
        wikiGraph: wikiGraph || { nodes: [], edges: [] },
        chatSessions: chatSessions || [],
        isLoadingWiki,
        isLoadingGraph,
        isLoadingChat,
        loadWikiPages,
        loadWikiGraph,
        loadChatSessions,
        invalidateAll
      }}
    >
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};
