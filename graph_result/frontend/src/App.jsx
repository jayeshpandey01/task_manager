import React, { useState } from 'react';
import GraphView from './components/GraphView';
import ChatInterface from './components/ChatInterface';
import axios from 'axios';

const backendUrl = 'http://localhost:8000';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [highlightNodes, setHighlightNodes] = useState([]);

  const loadOverview = async () => {
    try {
      const res = await axios.get(`${backendUrl}/api/graph/overview`);
      const { nodes, edges } = res.data;
      setGraphData({
        nodes: nodes.map(n => ({ 
          data: { id: n.id, label: n.id, labels: n.labels, properties: n.properties },
          classes: n.labels ? n.labels.join(' ') : ''
        })),
        edges: edges.map(e => ({ data: { id: `${e.source}-${e.target}-${e.type}`, source: e.source, target: e.target, label: e.type } }))
      });
    } catch (err) {
      console.error("Failed to load graph overview:", err);
    }
  };

  // Load initial graph on mount
  React.useEffect(() => {
    loadOverview();
  }, []);

  // Handles updating the visual graph from the Chat API results
  const handleChatDataUpdate = (data) => {
    // If we have query results, try to extract nodes/edges
    if (data.results && Array.isArray(data.results)) {
      const gData = convertNeo4jResultsToGraph(data.results);
      if (gData.nodes.length > 0) {
        setGraphData({
          nodes: gData.nodes,
          edges: gData.edges
        });
        // Highlight every node returned by the query for traceability
        const ids = gData.nodes.map(n => n.data.id);
        setHighlightNodes(ids);
      }
    }
  };

  const convertNeo4jResultsToGraph = (results) => {
    const nodesMap = {};
    const edgesMap = {};

    results.forEach(record => {
      for (const [key, value] of Object.entries(record)) {
        if (value && typeof value === 'object') {
          if (value.nodes && value.relationships) { // It's a Path
            value.nodes.forEach(node => {
              nodesMap[node.id] = { 
                data: { id: node.id, label: node.id, labels: node.labels, properties: node.properties },
                classes: node.labels ? node.labels.join(' ') : ''
              };
            });
            value.relationships.forEach(rel => {
              const edgeId = `${rel.source}-${rel.target}-${rel.type}`;
              edgesMap[edgeId] = { 
                data: { id: edgeId, source: rel.source, target: rel.target, label: rel.type, properties: rel.properties } 
              };
            });
          } else if (value.labels) { // It's a Node
            nodesMap[value.id] = { 
              data: { 
                id: value.id, 
                label: value.id, 
                labels: value.labels, 
                properties: value.properties 
              },
              classes: value.labels ? value.labels.join(' ') : ''
            };
          } else if (value.type && value.source && value.target) { // It's a Relationship
            const edgeId = `${value.source}-${value.target}-${value.type}`;
            edgesMap[edgeId] = { 
              data: { 
                id: edgeId, 
                source: value.source, 
                target: value.target, 
                label: value.type,
                properties: value.properties
              } 
            };
          }
        }
      }
    });

    return {
      nodes: Object.values(nodesMap),
      edges: Object.values(edgesMap)
    };
  };

  return (
    <div className="app-container">
      <GraphView 
        graphData={graphData} 
        setGraphData={setGraphData} 
        highlightNodes={highlightNodes} 
        resetGraph={loadOverview}
      />
      <ChatInterface 
        onDataUpdate={handleChatDataUpdate} 
        setHighlightNodes={setHighlightNodes}
      />
    </div>
  );
}

export default App;
