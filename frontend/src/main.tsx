import "@ant-design/v5-patch-for-react-19";
import "antd/dist/reset.css";
import "./styles.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import React from "react";
import ReactDOM from "react-dom/client";
import { AppRouter } from "./router/AppRouter";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider locale={ruRU}>
      <QueryClientProvider client={queryClient}>
        <AppRouter />
      </QueryClientProvider>
    </ConfigProvider>
  </React.StrictMode>
);

