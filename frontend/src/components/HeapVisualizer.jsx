import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const HeapVisualizer = ({ data }) => {
  const containerWidth = 800;
  const containerHeight = 350;
  const nodeRadius = 22;

  // Calculate coordinates for nodes using a simple tree layout algorithm
  const layoutTree = (node, depth, minX, maxX) => {
    if (!node) return null;
    
    const x = (minX + maxX) / 2;
    const y = depth * 70 + 40; // 70px vertical spacing, 40px top offset
    
    const layoutedNode = {
      ...node,
      x,
      y,
      childrenLayout: []
    };

    if (node.children && node.children.length > 0) {
      const numChildren = node.children.length;
      const step = (maxX - minX) / numChildren;
      
      node.children.forEach((child, index) => {
        const childMinX = minX + index * step;
        const childMaxX = minX + (index + 1) * step;
        const layoutedChild = layoutTree(child, depth + 1, childMinX, childMaxX);
        if (layoutedChild) {
          layoutedNode.childrenLayout.push(layoutedChild);
        }
      });
    }
    
    return layoutedNode;
  };

  const layoutedData = useMemo(() => {
    if (!data) return null;
    return layoutTree(data, 0, 0, containerWidth);
  }, [data]);

  // Extract edges and nodes as flat arrays for Framer Motion
  const getNodesAndEdges = (node) => {
    if (!node) return { nodes: [], edges: [] };
    
    let nodes = [{ id: node.id, x: node.x, y: node.y, priority: node.priority, name: node.name }];
    let edges = [];

    if (node.childrenLayout) {
      node.childrenLayout.forEach(child => {
        edges.push({ id: `e-${node.id}-${child.id}`, x1: node.x, y1: node.y, x2: child.x, y2: child.y });
        const childResult = getNodesAndEdges(child);
        nodes = nodes.concat(childResult.nodes);
        edges = edges.concat(childResult.edges);
      });
    }

    return { nodes, edges };
  };

  const { nodes, edges } = useMemo(() => getNodesAndEdges(layoutedData), [layoutedData]);

  if (!data) {
    return (
      <div className="treap-visualizer-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Queue is empty</p>
      </div>
    );
  }

  return (
    <div className="treap-visualizer-container">
      {/* Edges */}
      <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
        <AnimatePresence>
          {edges.map(edge => (
            <motion.line
              key={edge.id}
              x1={edge.x1}
              y1={edge.y1}
              x2={edge.x2}
              y2={edge.y2}
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="2"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1, x1: edge.x1, y1: edge.y1, x2: edge.x2, y2: edge.y2 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
            />
          ))}
        </AnimatePresence>
      </svg>

      {/* Nodes */}
      <AnimatePresence>
        {nodes.map(node => (
          <motion.div
            key={node.id}
            className="node"
            initial={{ scale: 0, opacity: 0, x: containerWidth / 2, y: 0 }}
            animate={{ 
              scale: 1, 
              opacity: 1, 
              x: node.x, 
              y: node.y 
            }}
            exit={{ scale: 0, opacity: 0, y: -50 }}
            transition={{ type: "spring", stiffness: 100, damping: 15 }}
            title={node.name}
          >
            <div className="node-priority">{node.priority}</div>
            {node.id % 100}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default HeapVisualizer;
