import React from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';

export interface DashboardGridProps {
  items: { id: string; content: React.ReactNode; }[];
  onReorder: (newOrder: string[]) => void;
}

const DashboardGrid: React.FC<DashboardGridProps> = ({ items, onReorder }) => {
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    const reordered = Array.from(items);
    const [removed] = reordered.splice(result.source.index, 1);
    if (!removed) return;
    reordered.splice(result.destination.index, 0, removed);
    onReorder(reordered.map(i => i.id));
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="dashboard" direction="horizontal">
        {(provided) => (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
               ref={provided.innerRef}
               {...provided.droppableProps}
          >
            {items.map((item, index) => (
              <Draggable key={item.id} draggableId={item.id} index={index}>
                {(draggableProvided, snapshot) => (
                  <div
                    ref={draggableProvided.innerRef}
                    {...draggableProvided.draggableProps}
                    {...draggableProvided.dragHandleProps}
                    className={`${snapshot.isDragging ? 'ring-2 ring-primary-400' : ''}`}
                  >
                    {item.content}
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
};

export default DashboardGrid;
