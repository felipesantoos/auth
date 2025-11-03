/**
 * Generic DataTable Component
 * Uses @tanstack/react-table with shadcn/ui styling
 * Supports sorting, filtering, and pagination
 * 
 * Compliance: 08d-ui-components.md Section 5
 */

import React from 'react';
import type {
  ColumnDef,
  SortingState,
  ColumnFiltersState} from '@tanstack/react-table';
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable
} from '@tanstack/react-table';
import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  searchPlaceholder?: string;
  searchColumn?: string;
}

/**
 * Generic Data Table Component
 * 
 * Features:
 * - Sorting: Click column headers to sort
 * - Filtering: Search box for filtering rows
 * - Pagination: Navigate through pages
 * - Type-safe: Generic TData and TValue
 * - Accessible: Semantic HTML with ARIA attributes
 * 
 * Performance: Memoized with React.memo to prevent re-renders
 * when parent components update but props haven't changed.
 * 
 * Example Usage:
 * ```tsx
 * <DataTable
 *   columns={userColumns}
 *   data={users}
 *   onEdit={(id) => openEditDialog(id)}
 *   onDelete={(id) => confirmDelete(id)}
 *   searchPlaceholder="Buscar usuários..."
 *   searchColumn="name"
 * />
 * ```
 */
// ⚡ PERFORMANCE: Memoized component to prevent re-renders
const DataTableInner = <TData, TValue>({
  columns,
  data,
  onEdit,
  onDelete,
  searchPlaceholder = 'Buscar...',
  searchColumn = 'name',
}: DataTableProps<TData, TValue>) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
    meta: {
      onEdit,
      onDelete,
    },
  });

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="flex items-center gap-4">
        <Input
          placeholder={searchPlaceholder}
          value={(table.getColumn(searchColumn)?.getFilterValue() as string) ?? ''}
          onChange={(event) =>
            table.getColumn(searchColumn)?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && 'selected'}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  Nenhum resultado encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {table.getFilteredRowModel().rows.length} resultado(s)
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="h-4 w-4" />
            Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Próximo
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

// Export memoized component with generic types support
export const DataTable = React.memo(DataTableInner) as typeof DataTableInner;

