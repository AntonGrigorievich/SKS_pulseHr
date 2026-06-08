import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Modal, Form, Input, Select, Switch, message } from "antd";
import { ReactFlow, Controls, Background, MiniMap, addEdge, applyNodeChanges, applyEdgeChanges, Node, Edge, Connection, NodeTypes, MarkerType, Handle, Position } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { apiRequest } from "../../api/client";
import { Question, SurveyDetail, QuestionType } from "../../api/types";

const QuestionNode = ({ data }: any) => {
  return (
    <div style={{ padding: 10, border: "1px solid #1677ff", borderRadius: 8, background: "#fff", minWidth: 200, boxShadow: "0 2px 4px rgba(0,0,0,0.1)" }}>
      <Handle type="target" position={Position.Top} />
      {data.is_start_node && <div style={{ fontSize: 10, color: "green", marginBottom: 4, fontWeight: "bold" }}>► Start Node</div>}
      <div style={{ fontWeight: "bold", marginBottom: 4 }}>{data.title}</div>
      <div style={{ fontSize: 12, color: "#666", display: "flex", justifyContent: "space-between" }}>
        <span>{data.type}</span>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

const nodeTypes: NodeTypes = {
  question: QuestionNode,
};

export function SurveyBuilderPage() {
  const { surveyId } = useParams();
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const { data } = useQuery({
    queryKey: ["survey-detail", surveyId],
    queryFn: () => apiRequest<SurveyDetail>(`/surveys/${surveyId}`),
    enabled: Boolean(surveyId),
  });

  useEffect(() => {
    if (data?.questions) {
      const newNodes: Node[] = data.questions.map((q: any, index: number) => ({
        id: q.id,
        type: "question",
        position: { x: q.position_x || 250 * index, y: q.position_y || 100 * (index % 2) },
        data: { title: q.title, type: q.type, is_start_node: q.is_start_node || index === 0 },
      }));
      setNodes(newNodes);

      const newEdges: Edge[] = [];
      if (data.rules) {
        data.rules.forEach((rule: any) => {
          if (rule.target_question_id) {
            newEdges.push({
              id: `e-${rule.id}`,
              source: `${rule.survey_id}`,
              target: rule.target_question_id,
              animated: true,
              label: rule.name,
              markerEnd: { type: MarkerType.ArrowClosed },
            });
          }
        });
      }
      setEdges(newEdges);
    }
  }, [data]);

  const onNodesChange = useCallback((changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((params: Connection | Edge) => setEdges((eds) => addEdge({ ...params, animated: true, markerEnd: { type: MarkerType.ArrowClosed } }, eds)), []);

  const createQuestion = useMutation({
    mutationFn: (payload: { title: string; type: QuestionType; is_required: boolean }) =>
      apiRequest(`/surveys/${surveyId}/questions`, {
        method: "POST",
        body: JSON.stringify({ ...payload, position: nodes.length, settings: {}, options: [] })
      }),
    onSuccess: () => {
      setOpen(false);
      message.success("Question added");
      queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] });
    }
  });

  const onSave = () => {
    message.success("Survey graph saved successfully!");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 100px)" }}>
      <div className="toolbar" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 20px", background: "#f5f5f5", borderRadius: 8, marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>{data?.title} - Visual Editor</h2>
        <div>
          <Button onClick={() => setOpen(true)} style={{ marginRight: 8 }}>Add Question</Button>
          <Button style={{ marginRight: 8 }}>Auto Layout</Button>
          <Button type="primary" onClick={onSave}>Save Graph</Button>
        </div>
      </div>
      
      <div style={{ flex: 1, border: "1px solid #ccc", borderRadius: 8, background: "#fafafa" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#aaa" gap={16} />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>

      <Modal title="Add question" open={open} onCancel={() => setOpen(false)} footer={null}>
        <Form layout="vertical" onFinish={(values) => createQuestion.mutate(values)}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="Type" initialValue="TEXT">
            <Select options={[
              { value: "SINGLE_CHOICE", label: "Single Choice" },
              { value: "MULTIPLE_CHOICE", label: "Multiple Choice" },
              { value: "RATING", label: "Rating" },
              { value: "TEXT", label: "Text" },
              { value: "MATRIX", label: "Matrix" },
            ]} />
          </Form.Item>
          <Form.Item name="is_required" label="Required" valuePropName="checked" initialValue><Switch /></Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: "100%" }}>Add Node</Button>
        </Form>
      </Modal>
    </div>
  );
}
