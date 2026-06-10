export const Progress = ({ value }: { value: number }) => <div className="h-2 bg-gray-200 rounded"><div className="h-full bg-blue-600 rounded" style={{ width: `${value}%` }} /></div>;
