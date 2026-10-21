import React from "react";

// A product screen — this comment's em-dash is not visible text.
export function RevenueTable({ rows }: { rows: { id: string; total: number }[] }) {
  return (
    <div className="bg-[#0f0f0f] p-4">
      <h2 className="text-[13px] font-medium">Revenue — last 30 days</h2>
      <table className="w-full">
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="transition-all hover:bg-[#FAFAF9]">
              <td>{r.id}</td>
              <td>{r.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <span onClick={() => alert("hi")}>More</span>
    </div>
  );
}
