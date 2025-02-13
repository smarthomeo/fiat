import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { X, Upload, Loader2, GripVertical } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import imageCompression from "browser-image-compression";
import { toast } from "@/components/ui/use-toast";

interface ImageUploadProps {
  value: string[];
  onChange: (urls: string[]) => void;
  onRemove: (url: string) => void;
  maxFiles?: number;
  title: string;
}

const ImageUpload = ({ 
  value = [],
  onChange, 
  onRemove, 
  maxFiles = 5,
  title
}: ImageUploadProps) => {
  const [loading, setLoading] = useState(false);

  const compressImage = async (file: File) => {
    const options = {
      maxSizeMB: 1,
      maxWidthOrHeight: 1920,
      useWebWorker: true
    };
    
    try {
      return await imageCompression(file, options);
    } catch (error) {
      console.error("Error compressing image:", error);
      return file;
    }
  };

  const onUpload = async (file: File) => {
    try {
      // Create a new filename with extension
      const extension = file.name.split('.').pop() || 'jpg';
      const newFile = new File([file], `${title || 'upload'}.${extension}`, {
        type: file.type
      });

      const formData = new FormData();
      formData.append('image', newFile);
      formData.append('title', title || 'upload');

      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }

      const data = await response.json();
      // In production, use the BACKEND_URL, in development use the relative path
      const baseUrl = import.meta.env.PROD 
        ? import.meta.env.VITE_BACKEND_URL 
        : import.meta.env.VITE_API_URL.replace('/api', '');
      const fullUrl = `${baseUrl}${data.url}`;
      const newUrls = [...value, fullUrl].filter(Boolean); // Filter out undefined/null values
      onChange(newUrls);
    } catch (error) {
      console.error('Upload error:', error);
      toast({
        title: "Error",
        description: "Failed to upload image",
        variant: "destructive",
      });
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (value.length + acceptedFiles.length > maxFiles) {
      toast({
        title: "Error",
        description: `You can only upload up to ${maxFiles} images`,
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      for (const file of acceptedFiles) {
        const compressedFile = await compressImage(file);
        await onUpload(compressedFile);
      }
    } catch (error) {
      console.error('Error uploading images:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to upload images',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [value, onChange, maxFiles]);

  const onDragEnd = (result: any) => {
    if (!result.destination) return;

    const items = Array.from(value);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    onChange(items);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif']
    },
    maxFiles: maxFiles - value.length,
    disabled: loading
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 cursor-pointer
          transition-colors duration-200 ease-in-out
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300'}
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center text-sm text-gray-600">
          {loading ? (
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
          ) : (
            <>
              <Upload className="h-10 w-10 mb-2 text-gray-400" />
              <p className="font-medium">
                {isDragActive ? "Drop images here" : "Drag & drop images here"}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                or click to select files
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {`${value.length}/${maxFiles} images uploaded`}
              </p>
            </>
          )}
        </div>
      </div>
      
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="images" direction="horizontal">
          {(provided) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              className="grid grid-cols-2 md:grid-cols-3 gap-4"
            >
              {(value || []).map((url, index) => {
                if (!url) return null;
                // In production, use the BACKEND_URL, in development use the relative path
                const baseUrl = import.meta.env.PROD 
                  ? import.meta.env.VITE_BACKEND_URL 
                  : import.meta.env.VITE_API_URL.replace('/api', '');
                const imageUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
                
                return (
                  <Draggable 
                    key={`image-${index}`} 
                    draggableId={`image-${index}`} 
                    index={index}
                  >
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        className="relative group aspect-square"
                      >
                        <div
                          {...provided.dragHandleProps}
                          className="absolute top-2 left-2 p-1 rounded-full bg-white/80 
                                   hover:bg-white shadow-sm opacity-0 group-hover:opacity-100 
                                   transition-opacity duration-200 cursor-grab"
                        >
                          <GripVertical className="w-4 h-4" />
                        </div>
                        <img
                          src={imageUrl}
                          alt={`Upload ${index + 1}`}
                          className="w-full h-full object-cover rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={() => onRemove(url)}
                          className="absolute top-2 right-2 p-1 rounded-full bg-white/80 
                                   hover:bg-white shadow-sm opacity-0 group-hover:opacity-100 
                                   transition-opacity duration-200"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </Draggable>
                );
              })}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </div>
  );
};

export default ImageUpload; 