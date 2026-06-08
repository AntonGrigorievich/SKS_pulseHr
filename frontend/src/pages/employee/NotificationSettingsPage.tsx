import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Form, Input, Switch } from "antd";
import { apiRequest } from "../../api/client";

interface Settings {
  push_enabled: boolean;
  telegram_enabled: boolean;
  email_enabled: boolean;
  sms_enabled: boolean;
  telegram_chat_id: string | null;
  email: string | null;
}

export function NotificationSettingsPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["notification-settings"], queryFn: () => apiRequest<Settings>("/notifications/settings") });
  const mutation = useMutation({
    mutationFn: (payload: Partial<Settings>) =>
      apiRequest("/notifications/settings", { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notification-settings"] })
  });

  return (
    <Card title="Notification Settings">
      <Form layout="vertical" key={JSON.stringify(data)} initialValues={data} onFinish={(values) => mutation.mutate(values)}>
        <Form.Item name="push_enabled" label="Push" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="telegram_enabled" label="Telegram" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="telegram_chat_id" label="Telegram chat"><Input /></Form.Item>
        <Form.Item name="email_enabled" label="Email" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="email" label="Email address"><Input /></Form.Item>
        <Form.Item name="sms_enabled" label="SMS" valuePropName="checked"><Switch /></Form.Item>
        <Button type="primary" htmlType="submit">Save</Button>
      </Form>
    </Card>
  );
}
