import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { apiRequest } from "../api/client";
import { TokenPair } from "../api/types";
import { useAuthStore } from "../stores/authStore";

const schema = z.object({
  phone: z.string().min(5),
  code: z.string().regex(/^\d{6}$/).optional()
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);
  const form = useForm<LoginForm>({ resolver: zodResolver(schema), defaultValues: { phone: "" } });

  const sendCode = useMutation({
    mutationFn: (phone: string) =>
      apiRequest("/auth/send-code", { method: "POST", body: JSON.stringify({ phone }) }),
    onSuccess: () => message.success("OTP generated")
  });

  const verifyCode = useMutation({
    mutationFn: (payload: Required<LoginForm>) =>
      apiRequest<TokenPair>("/auth/verify-code", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/employee");
    }
  });

  const phone = form.watch("phone");

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <Card style={{ width: 420 }}>
        <Typography.Title level={2}>PulseHR</Typography.Title>
        <Form layout="vertical" onFinish={form.handleSubmit((values) => verifyCode.mutate(values as Required<LoginForm>))}>
          <Form.Item label="Phone">
            <Controller name="phone" control={form.control} render={({ field }) => <Input {...field} />} />
          </Form.Item>
          <Form.Item label="OTP">
            <Controller name="code" control={form.control} render={({ field }) => <Input {...field} maxLength={6} />} />
          </Form.Item>
          <Button block onClick={() => sendCode.mutate(phone)} loading={sendCode.isPending}>
            Send code
          </Button>
          <Button block type="primary" htmlType="submit" loading={verifyCode.isPending} style={{ marginTop: 12 }}>
            Login
          </Button>
        </Form>
      </Card>
    </div>
  );
}

