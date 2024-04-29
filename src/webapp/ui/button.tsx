import clsx from 'clsx';

export default function Button({
  kind = 'default',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  kind?: 'default' | 'detection' | 'detecting' | 'delete';
}) {
  return (
    <button
      className={clsx('rounded-lg px-3 py-1 text-sm font-medium', {
        'bg-gray-700 text-gray-100 hover:bg-gray-500 hover:text-white':
          kind === 'default',
        'bg-blue-900 text-red-50 float-right':
          kind === 'detecting',
        'bg-green-900 text-red-50 float-right hover:bg-green-600 hover:text-white':
          kind === 'detection',
        'bg-red-900 text-red-50 float-right ms-4 hover:bg-red-600 hover:text-white':
          kind === 'delete',
      })}
      {...props}
    />
  );
}
