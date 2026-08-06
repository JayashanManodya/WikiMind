import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getWikiIndex, getWikiGraph, getChatSessions, getDocumentStatus } from '../api/client';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [wikiPages, setWikiPages] = useState(null);
  const [wikiGraph, setWikiGraph] = useState(null);
  const [chatSessions, setChatSessions] = useState(null);

  const [isLoadingWiki, setIsLoadingWiki] = useState(false);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Background Task & Toast Notification State
  const [activeProcessingTasks, setActiveProcessingTasks] = useState([]); // [{ fileId, filename }]
  const [toastNotification, setToastNotification] = useState(null);

  // Invalidate all cached data on new document upload
  const invalidateAll = useCallback(() => {
    setWikiPages(null);
    setWikiGraph(null);
    setChatSessions(null);
  }, []);

  const addProcessingTask = useCallback((fileId, filename) => {
    setActiveProcessingTasks((prev) => [...prev, { fileId, filename }]);
    setToastNotification({
      id: fileId,
      status: 'processing',
      title: 'Ingesting Document...',
      message: `File '${filename}' is processing in the background. You can navigate anywhere.`
    });
  }, []);

  const dismissToast = useCallback(() => {
    setToastNotification(null);
  }, []);

  // Poll background processing tasks
  useEffect(() => {
    if (activeProcessingTasks.length === 0) return;

    const interval = setInterval(async () => {
      for (const task of activeProcessingTasks) {
        try {
          const statusRes = await getDocumentStatus(task.fileId);
          if (statusRes.status === 'fully_processed') {
            // Remove task from active list
            setActiveProcessingTasks((prev) => prev.filter((t) => t.fileId !== task.fileId));
            invalidateAll();
            setToastNotification({
              id: task.fileId,
              status: 'fully_processed',
              title: 'Document Ingestion Complete!',
              message: `File '${task.filename}' processed successfully! ${statusRes.pages_created.length} new Wiki pages created.`,
              filename: task.filename,
              pages_created: statusRes.pages_created
            });
          } else if (statusRes.status === 'failed') {
            setActiveProcessingTasks((prev) => prev.filter((t) => t.fileId !== task.fileId));
            setToastNotification({
              id: task.fileId,
              status: 'failed',
              title: 'Ingestion Failed',
              message: `Failed to process '${task.filename}': ${statusRes.error || 'Unknown error'}`
            });
          }
        } catch (err) {
          console.error(`Error polling status for ${task.fileId}:`, err);
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [activeProcessingTasks, invalidateAll]);

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
        invalidateAll,
        activeProcessingTasks,
        toastNotification,
        addProcessingTask,
        dismissToast
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

