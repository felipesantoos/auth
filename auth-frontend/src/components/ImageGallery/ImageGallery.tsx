/**
 * ImageGallery Component
 * Display user's images in a responsive grid
 */

import React, { useState } from 'react';
import { Trash2, Download, Share2 } from 'lucide-react';
import { useFileList } from '../../hooks/useFileList';
import { formatFileSize } from '../../utils/file';
import { FileInfo } from '../../types/file';

interface ImageGalleryProps {
  onImageClick?: (image: FileInfo) => void;
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({ onImageClick }) => {
  const { files, loading, deleteFile, refresh } = useFileList('image');
  const [selectedImage, setSelectedImage] = useState<FileInfo | null>(null);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Deletar esta imagem?')) return;

    try {
      await deleteFile(id);
    } catch (error) {
      alert('Falha ao deletar imagem');
    }
  };

  const handleImageClick = (image: FileInfo) => {
    if (onImageClick) {
      onImageClick(image);
    } else {
      setSelectedImage(image);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Carregando...</div>;
  }

  if (files.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Nenhuma imagem encontrada
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {files.map(image => (
          <div
            key={image.id}
            className="group relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
            onClick={() => handleImageClick(image)}
          >
            <img
              src={image.url}
              alt={image.filename}
              className="w-full h-full object-cover"
              loading="lazy"
            />

            {/* Overlay on hover */}
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
              <button
                onClick={(e) => handleDelete(image.id, e)}
                className="p-2 bg-red-500 hover:bg-red-600 rounded-full text-white"
                title="Deletar"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            {/* Info */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <p className="text-white text-xs truncate">{image.filename}</p>
              <p className="text-white/70 text-xs">{formatFileSize(image.size)}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-5xl max-h-full">
            <img
              src={selectedImage.url}
              alt={selectedImage.filename}
              className="max-w-full max-h-[90vh] object-contain"
            />
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

