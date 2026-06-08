import { Checkbox, Form, Input, Radio, Rate, Table } from "antd";
import { Question } from "../api/types";

interface Props {
  question: Question;
  value?: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
}

export function QuestionRenderer({ question, value, onChange }: Props) {
  if (question.type === "SINGLE_CHOICE") {
    return (
      <Radio.Group value={value?.option} onChange={(event) => onChange({ option: event.target.value })}>
        {question.options.map((option) => (
          <Radio key={option.value} value={option.value}>
            {option.label}
          </Radio>
        ))}
      </Radio.Group>
    );
  }

  if (question.type === "MULTIPLE_CHOICE") {
    return (
      <Checkbox.Group
        value={(value?.options as string[]) ?? []}
        options={question.options.map((option) => ({ label: option.label, value: option.value }))}
        onChange={(options) => onChange({ options })}
      />
    );
  }

  if (question.type === "RATING") {
    return <Rate count={Number(question.settings.max ?? 10)} value={Number(value?.score ?? 0)} onChange={(score) => onChange({ score })} />;
  }

  if (question.type === "MATRIX") {
    const rows = (question.settings.rows as string[]) ?? [];
    const columns = (question.settings.columns as string[]) ?? ["1", "2", "3", "4", "5"];
    return (
      <Table
        pagination={false}
        rowKey="row"
        dataSource={rows.map((row) => ({ row }))}
        columns={[
          { title: "", dataIndex: "row" },
          ...columns.map((column) => ({
            title: column,
            render: (_: unknown, record: { row: string }) => (
              <Radio
                checked={(value?.rows as Record<string, string> | undefined)?.[record.row] === column}
                onChange={() => onChange({ rows: { ...((value?.rows as object) ?? {}), [record.row]: column } })}
              />
            )
          }))
        ]}
      />
    );
  }

  return (
    <Form.Item>
      <Input.TextArea value={(value?.text as string) ?? ""} rows={4} onChange={(event) => onChange({ text: event.target.value })} />
    </Form.Item>
  );
}

