/**
 * FilesPage
 * File management page with upload and gallery
 */

import React, { useState } from 'react';
import { FileUpload } from '../../components/FileUpload/FileUpload';
import { ImageGallery } from '../../components/ImageGallery/ImageGallery';
import type { FileType } from '../../types/file';

export const FilesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<FileType>('all');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = (urls: string[]) => {
    console.log('Files uploaded:', urls);
    // Refresh file list
    setRefreshKey(prev => prev + 1);
  };

  const tabs: { label: string; value: FileType }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Imagens', value: 'image' },
    { label: 'Vídeos', value: 'video' },
    { label: 'Documentos', value: 'document' },
  ];

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Meus Arquivos</h1>
        <p className="text-gray-600">
          Gerencie seus arquivos, imagens e documentos
        </p>
      </div>

      {/* Upload Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Enviar Arquivos</h2>
        <FileUpload
          maxSize={100}
          maxFiles={10}
          onUpload={handleUploadSuccess}
          multiple={true}
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-4">
          {tabs.map(tab => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`
                px-4 py-2 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab.value
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* File Gallery/List */}
      <div key={refreshKey}>
        {activeTab === 'image' ? (
          <ImageGallery />
        ) : (
          <div className="text-center py-12 text-gray-500">
            Visualização de {tabs.find(t => t.value === activeTab)?.label} em desenvolvimento
          </div>
        )}
      </div>
    </div>
  );
};

