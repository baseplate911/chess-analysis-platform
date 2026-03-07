import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function WinProbabilityChart({ winProbabilities = [] }) {
  if (!winProbabilities.length) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    );
  }

  const data = winProbabilities.map((d) => ({
    move: d.move,
    White: parseFloat((d.white).toFixed(1)),
    Draw: parseFloat((d.draw).toFixed(1)),
    Black: parseFloat((d.black).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="move"
          tick={{ fill: '#9ca3af', fontSize: 10 }}
          label={{ value: 'Move', position: 'insideBottom', offset: -2, fill: '#9ca3af', fontSize: 10 }}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#9ca3af', fontSize: 10 }}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
          labelStyle={{ color: '#e5e7eb', fontSize: 12 }}
          itemStyle={{ fontSize: 11 }}
          formatter={(value) => [`${value}%`]}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
        <Line type="monotone" dataKey="White" stroke="#60a5fa" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Draw" stroke="#9ca3af" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Black" stroke="#f87171" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
