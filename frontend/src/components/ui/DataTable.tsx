import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState } from '@tanstack/react-table'
import { ChevronDownIcon, ChevronUpIcon, ChevronsUpDownIcon } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/cn'

interface DataTableProps<T> {
  columns: ColumnDef<T, unknown>[]
  data: T[]
  onRowClick?: (row: T) => void
  stickyFirstColumn?: boolean
  getRowId?: (row: T) => string
}

export function DataTable<T>({ columns, data, onRowClick, stickyFirstColumn, getRowId }: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([])

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId,
  })

  return (
    <div className="scroll-thin overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-border">
              {headerGroup.headers.map((header, colIndex) => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  className={cn(
                    'whitespace-nowrap px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-muted',
                    header.column.getCanSort() && 'cursor-pointer select-none hover:text-text-secondary',
                    stickyFirstColumn && colIndex === 0 && 'sticky left-0 z-10 bg-surface',
                  )}
                >
                  {header.isPlaceholder ? null : (
                    <span className="inline-flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() &&
                        ({
                          asc: <ChevronUpIcon className="h-3 w-3" />,
                          desc: <ChevronDownIcon className="h-3 w-3" />,
                        }[header.column.getIsSorted() as string] ?? (
                          <ChevronsUpDownIcon className="h-3 w-3 opacity-40" />
                        ))}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row.original)}
              className={cn('border-b border-border last:border-0', onRowClick && 'cursor-pointer hover:bg-hover')}
            >
              {row.getVisibleCells().map((cell, colIndex) => (
                <td
                  key={cell.id}
                  className={cn(
                    'whitespace-nowrap px-3 py-2 text-text-primary',
                    stickyFirstColumn && colIndex === 0 && 'sticky left-0 z-10 bg-surface',
                  )}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
