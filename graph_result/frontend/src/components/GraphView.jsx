import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import CytoscapeComponent from 'react-cytoscapejs';
import { Search, Maximize, RefreshCw } from 'lucide-react';
import axios from 'axios';

cytoscape.use(dagre);

const backendUrl = 'http://localhost:8000';

const GraphView = ({ graphData, setGraphData, highlightNodes, resetGraph }) => {
  const cyRef = useRef(null);
  const [searchId, setSearchId] = useState('');
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, data: null });

  const fetchNeighbors = async (nodeId) => {
    try {
      const res = await axios.get(`${backendUrl}/api/graph/neighbors/${encodeURIComponent(nodeId)}`);
      const { nodes, edges } = res.data;
      
      const newNodes = nodes.map(n => ({
        data: { id: n.id, label: n.id, labels: n.labels, properties: n.properties },
        classes: n.labels ? n.labels.join(' ') : ''
      }));
      
      const newEdges = edges.map(e => ({
        data: { source: e.source, target: e.target, label: e.type, id: `${e.source}-${e.target}-${e.type}` }
      }));

      // Merge data
      setGraphData(prev => {
        const existingNodeIds = new Set(prev.nodes.map(n => n.data.id));
        const existingEdgeIds = new Set(prev.edges.map(e => e.data.id));
        
        const mergedNodes = [...prev.nodes, ...newNodes.filter(n => !existingNodeIds.has(n.data.id))];
        const mergedEdges = [...prev.edges, ...newEdges.filter(e => !existingEdgeIds.has(e.data.id))];
        
        return { nodes: mergedNodes, edges: mergedEdges };
      });

    } catch (e) {
      console.error(e);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchId.trim()) {
      resetGraph();
      return;
    }

    try {
      const res = await axios.get(`${backendUrl}/api/graph/search?q=${encodeURIComponent(searchId)}`);
      const { nodes, edges } = res.data;
      
      if (nodes && nodes.length > 0) {
        // If we found nodes, set them as the new graph
        const searchNodes = nodes.map(n => ({
          data: { id: n.id, label: n.id, labels: n.labels, properties: n.properties },
          classes: (n.labels ? n.labels.join(' ') : '') + (n.id === searchId ? ' highlighted' : '')
        }));
        
        const searchEdges = edges.map(e => ({
          data: { id: `${e.source}-${e.target}-${e.type}`, source: e.source, target: e.target, label: e.type }
        }));

        setGraphData({ nodes: searchNodes, edges: searchEdges });
        
        // Ensure we fit the result
        setTimeout(() => {
          if (cyRef.current) {
            cyRef.current.fit();
            // Optional: specifically highlight the exact match if it exists
            const match = cyRef.current.nodes().filter(n => n.id() === searchId || n.data('properties')?.name === searchId);
            match.addClass('highlighted');
          }
        }, 500);
      } else {
        // Fallback or Alert
        console.log("No nodes found for search query:", searchId);
      }
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  useEffect(() => {
    if (cyRef.current) {
        // Run layout
        cyRef.current.layout({
            name: 'dagre',
            rankDir: 'LR',
            padding: 50,
            animate: true,
            fit: true,
            nodeSep: 60,
            rankSep: 120
        }).run();
    }
  }, [graphData]);

  // Apply/remove 'highlighted' class on nodes when query result changes
  useEffect(() => {
    if (!cyRef.current) return;
    // Clear all existing highlights
    cyRef.current.nodes().removeClass('highlighted');
    if (highlightNodes && highlightNodes.length > 0) {
      const idSet = new Set(highlightNodes);
      cyRef.current.nodes().forEach(node => {
        if (idSet.has(node.id())) {
          node.addClass('highlighted');
        }
      });
    }
  }, [highlightNodes]);

  const stylesheet = [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'color': '#f0f0f5',
        'text-outline-width': 2,
        'text-outline-color': '#1a1a24',
        'font-size': '10px',
        'background-color': '#888',
        'width': 30,
        'height': 30,
        'border-width': 2,
        'border-color': '#fff'
      }
    },
    {
      selector: '.Customer',
      style: { 'background-color': '#e06c75' }
    },
    {
      selector: '.SalesOrder',
      style: { 'background-color': '#e5c07b' }
    },
    {
      selector: '.SalesOrderItem',
      style: { 'background-color': '#d19a66' }
    },
    {
      selector: '.OutboundDelivery',
      style: { 'background-color': '#98c379' }
    },
    {
      selector: '.OutboundDeliveryItem',
      style: { 'background-color': '#b5eaa0' }
    },
    {
      selector: '.BillingDocument',
      style: { 'background-color': '#61afef' }
    },
    {
      selector: '.BillingDocumentItem',
      style: { 'background-color': '#5bc0de' }
    },
    {
      selector: '.AccountingDocument',
      style: { 'background-color': '#c678dd' }
    },
    {
      selector: '.Product',
      style: { 'background-color': '#56b6c2' }
    },
    {
      selector: '.highlighted',
      style: {
        'border-width': 6,
        'border-color': '#6366f1',
        'width': 45,
        'height': 45,
        'z-index': 999
      }
    },

    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#445',
        'target-arrow-color': '#445',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '8px',
        'color': '#88a',
        'text-rotation': 'autorotate',
        'text-background-opacity': 1,
        'text-background-color': '#1a1a24',
        'text-background-shape': 'roundrectangle'
      }
    }
  ];

  const handleNodeClick = (e) => {
    const node = e.target;
    fetchNeighbors(node.id());
  };

  const handleNodeHover = (e) => {
    const node = e.target;
    const bb = node.renderedBoundingBox();
    setTooltip({
      visible: true,
      x: bb.x1 + (bb.w/2),
      y: bb.y2 + 10,
      data: node.data()
    });
  };

  const handleNodeOut = () => {
    setTooltip({ visible: false, x: 0, y: 0, data: null });
  };

  return (
    <div className="graph-container">
      <div className="graph-top-bar">
        <form onSubmit={handleSearch} style={{display:'flex', gap:'10px'}}>
          <input 
            type="text" 
            placeholder="Search Node ID (e.g. Sales Order #)" 
            className="search-input"
            value={searchId}
            onChange={e => setSearchId(e.target.value)}
          />
          <button type="submit" className="icon-btn" title="Search"><Search size={18} /></button>
        </form>
        <button className="icon-btn" onClick={resetGraph} title="Reset to Overview"><RefreshCw size={18} /></button>
        <button className="icon-btn" onClick={() => cyRef.current?.fit()} title="Fit View"><Maximize size={18} /></button>
      </div>

      <CytoscapeComponent 
        elements={CytoscapeComponent.normalizeElements(graphData)} 
        style={{ width: '100%', height: '100%' }}
        stylesheet={stylesheet}
        cy={(cy) => {
          cyRef.current = cy;
          cy.on('tap', 'node', handleNodeClick);
          cy.on('mouseover', 'node', handleNodeHover);
          cy.on('mouseout', 'node', handleNodeOut);
        }}
        wheelSensitivity={1}
      />

      <div className="legend-panel">
        <div className="panel-title">Node Types</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#e06c75'}}></div> Customer</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#e5c07b'}}></div> Sales Order</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#d19a66'}}></div> Sales Order Item</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#98c379'}}></div> Delivery</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#b5eaa0'}}></div> Delivery Item</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#61afef'}}></div> Billing</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#5bc0de'}}></div> Billing Item</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#c678dd'}}></div> Journal Entry / Payment</div>
        <div className="legend-item"><div className="legend-color" style={{backgroundColor: '#56b6c2'}}></div> Product</div>
      </div>

      {tooltip.visible && tooltip.data && (
        <div className="node-tooltip visible" style={{ left: tooltip.x, top: tooltip.y }}>
          <div className="tooltip-header">
            <div className="tooltip-title">
              {tooltip.data.id}
              <span className="tooltip-badge">{(tooltip.data.labels && tooltip.data.labels[0]) || 'Node'}</span>
            </div>
          </div>
          <div>
            {tooltip.data.properties && Object.entries(tooltip.data.properties).slice(0, 5).map(([k, v]) => (
              <div className="tooltip-row" key={k}>
                <span className="tooltip-key">{k}</span>
                <span className="tooltip-value">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphView;
