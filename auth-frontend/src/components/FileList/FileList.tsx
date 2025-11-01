/**
 * FileList Component
 * Display files in table/card format with actions
 */
import React, { useState } from 'react';
import { FileInfo, FileSortField } from '../../types/file';
import { formatFileSize } from '../../utils/file';
import './FileList.css';

interface FileListProps {
  files: FileInfo[];
  onDelete?: (fileId: string) => Promise<void>;
  onDownload?: (fileId: string) => void;
  onShare?: (fileId: string) => void;
  loading?: boolean;
  viewMode?: 'table' | 'cards';
}

export const FileList: React.FC<FileListProps> = ({
  files,
  onDelete,
  onDownload,
  onShare,
  loading = false,
  viewMode = 'table'
}) => {
  const [sortField, setSortField] = useState<FileSortField>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filterType, setFilterType] = useState<string>('all');
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

  // Sort files
  const sortedFiles = [...files].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    const multiplier = sortDirection === 'asc' ? 1 : -1;
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return aValue.localeCompare(bValue) * multiplier;
    }
    return (aValue > bValue ? 1 : -1) * multiplier;
  });

  // Filter files by type
  const filteredFiles = filterType === 'all'
    ? sortedFiles
    : sortedFiles.filter(f => f.mime_type.startsWith(filterType));

  const toggleSort = (field: FileSortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const toggleFileSelection = (fileId: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const handleBulkDelete = async () => {
    if (!onDelete) return;
    for (const fileId of selectedFiles) {
      await onDelete(fileId);
    }
    setSelectedFiles(new Set());
  };

  if (loading) {
    return <div className="file-list-loading">Loading files...</div>;
  }

  if (files.length === 0) {
    return <div className="file-list-empty">No files yet</div>;
  }

  return (
    <div className="file-list">
      {/* Filter Controls */}
      <div className="file-list-controls">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="file-filter"
        >
          <option value="all">All Files</option>
          <option value="image">Images</option>
          <option value="video">Videos</option>
          <option value="audio">Audio</option>
          <option value="application">Documents</option>
        </select>

        {selectedFiles.size > 0 && (
          <button onClick={handleBulkDelete} className="btn-delete-bulk">
            Delete Selected ({selectedFiles.size})
          </button>
        )}
      </div>

      {/* Table View */}
      {viewMode === 'table' && (
        <table className="file-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedFiles(new Set(filteredFiles.map(f => f.id)));
                    } else {
                      setSelectedFiles(new Set());
                    }
                  }}
                />
              </th>
              <th onClick={() => toggleSort('original_filename')}>
                Name {sortField === 'original_filename' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('mime_type')}>
                Type {sortField === 'mime_type' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('file_size')}>
                Size {sortField === 'file_size' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('created_at')}>
                Date {sortField === 'created_at' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredFiles.map((file) => (
              <tr key={file.id}>
                <td>
                  <input
                    type="checkbox"
                    checked={selectedFiles.has(file.id)}
                    onChange={() => toggleFileSelection(file.id)}
                  />
                </td>
                <td>{file.original_filename}</td>
                <td>{file.mime_type}</td>
                <td>{formatFileSize(file.file_size)}</td>
                <td>{new Date(file.created_at).toLocaleDateString()}</td>
                <td className="file-actions">
                  {onDownload && (
                    <button onClick={() => onDownload(file.id)} className="btn-action">
                      Download
                    </button>
                  )}
                  {onShare && (
                    <button onClick={() => onShare(file.id)} className="btn-action">
                      Share
                    </button>
                  )}
                  {onDelete && (
                    <button onClick={() => onDelete(file.id)} className="btn-action btn-delete">
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Card View */}
      {viewMode === 'cards' && (
        <div className="file-cards">
          {filteredFiles.map((file) => (
            <div key={file.id} className="file-card">
              <input
                type="checkbox"
                checked={selectedFiles.has(file.id)}
                onChange={() => toggleFileSelection(file.id)}
                className="file-card-checkbox"
              />
              
              <div className="file-card-preview">
                {file.mime_type.startsWith('image/') ? (
                  <img src={file.url} alt={file.original_filename} />
                ) : (
                  <div className="file-icon">{file.mime_type.split('/')[0]}</div>
                )}
              </div>
              
              <div className="file-card-info">
                <h4>{file.original_filename}</h4>
                <p>{formatFileSize(file.file_size)}</p>
                <p>{new Date(file.created_at).toLocaleDateString()}</p>
              </div>
              
              <div className="file-card-actions">
                {onDownload && (
                  <button onClick={() => onDownload(file.id)}>Download</button>
                )}
                {onShare && (
                  <button onClick={() => onShare(file.id)}>Share</button>
                )}
                {onDelete && (
                  <button onClick={() => onDelete(file.id)} className="btn-delete">
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

