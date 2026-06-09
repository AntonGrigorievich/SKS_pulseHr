import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Form, Input, Modal, Space, Table, Tag } from "antd";
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { Survey } from "../../api/types";

export function SurveyManagementPage() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data = [] } = useQuery({ queryKey: ["surveys"], queryFn: () => apiRequest<Survey[]>("/surveys") });
  const create = useMutation({
    mutationFn: (payload: Partial<Survey>) => apiRequest("/surveys", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: ["surveys"] });
    }
  });
  const action = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => apiRequest(`/surveys/${id}/${name}`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["surveys"] })
  });

  return (
    <>
      <div className="toolbar">
        <h2>Survey Management</h2>
        <Button icon={<PlusOutlined />} type="primary" onClick={() => setOpen(true)}>Create</Button>
      </div>
      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: "Title", dataIndex: "title" },
          { title: "Status", dataIndex: "status", render: (surveyStatus: Survey["status"]) => <Tag>{surveyStatus}</Tag> },
          { title: "Anonymous", dataIndex: "is_anonymous", render: (value) => (value ? "Yes" : "No") },
          {
            title: "Actions",
            render: (_value: unknown, record: Survey) => (
              <Space>
                <Link to={`/hr/surveys/${record.id}/builder`}>Builder</Link>
                <Link to={`/hr/analytics?surveyId=${record.id}`}>Analytics</Link>
                <Button size="small" onClick={() => action.mutate({ id: record.id, name: "publish" })}>Publish</Button>
                <Button size="small" onClick={() => action.mutate({ id: record.id, name: "close" })}>Close</Button>
                <Button size="small" onClick={() => action.mutate({ id: record.id, name: "archive" })}>Archive</Button>
              </Space>
            )
          }
        ]}
      />
      <Modal title="Create survey" open={open} onCancel={() => setOpen(false)} footer={null}>
        <Form layout="vertical" onFinish={(values) => create.mutate(values)}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          <Form.Item name="estimated_minutes" label="Minutes" initialValue={5}><Input type="number" /></Form.Item>
          <Button type="primary" htmlType="submit">Create</Button>
        </Form>
      </Modal>
    </>
  );
}
