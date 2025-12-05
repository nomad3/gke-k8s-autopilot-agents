import React, { useState, useRef, useEffect } from 'react';
import { CheckIcon, ChevronDownIcon, XMarkIcon } from '@heroicons/react/24/outline';

export interface Practice {
  practice_location: string;
  total_production?: number;
}

export interface PracticeSelectorProps {
  practices: Practice[];
  selectedPractices: string[];
  onChange: (selected: string[]) => void;
  minSelect?: number;
  maxSelect?: number;
  loading?: boolean;
}

/**
 * PracticeSelector - Multi-select dropdown for practice comparison
 * Allows selection of 2-5 practices for side-by-side comparison
 */
export const PracticeSelector: React.FC<PracticeSelectorProps> = ({
  practices,
  selectedPractices,
  onChange,
  minSelect = 2,
  maxSelect = 5,
  loading = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Filter practices based on search
  const filteredPractices = practices.filter(p =>
    p.practice_location.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Toggle practice selection
  const togglePractice = (location: string) => {
    if (selectedPractices.includes(location)) {
      // Remove if already selected
      onChange(selectedPractices.filter(p => p !== location));
    } else {
      // Add if under max limit
      if (selectedPractices.length < maxSelect) {
        onChange([...selectedPractices, location]);
      }
    }
  };

  // Remove a practice
  const removePractice = (location: string) => {
    onChange(selectedPractices.filter(p => p !== location));
  };

  // Clear all selections
  const clearAll = () => {
    onChange([]);
  };

  // Loading state
  if (loading) {
    return (
      <div className="w-full px-4 py-3 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse">
        <div className="w-48 h-4 bg-gray-300 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  const canSelectMore = selectedPractices.length < maxSelect;
  const meetsMinimum = selectedPractices.length >= minSelect;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <div className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        >
          <div className="flex-1 text-left">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              Select Practices to Compare
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {selectedPractices.length} of {maxSelect} selected
              {!meetsMinimum && ` (minimum ${minSelect})`}
            </div>
          </div>
          <ChevronDownIcon
            className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {/* Selected Practices Pills */}
        {selectedPractices.length > 0 && (
          <div className="px-4 pb-3 flex flex-wrap gap-2">
            {selectedPractices.map((location) => (
              <div
                key={location}
                className="inline-flex items-center space-x-1 px-3 py-1 bg-sky-100 dark:bg-sky-900/30 text-sky-800 dark:text-sky-300 rounded-full text-sm"
              >
                <span>{location}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removePractice(location);
                  }}
                  className="ml-1 hover:text-sky-600 dark:hover:text-sky-200"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            ))}

            {selectedPractices.length > 0 && (
              <button
                onClick={clearAll}
                className="inline-flex items-center px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                Clear all
              </button>
            )}
          </div>
        )}
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 mt-2 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl max-h-96 overflow-hidden">
          {/* Search Input */}
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search practices..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          {/* Practice List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredPractices.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                <p className="text-sm">No practices found</p>
              </div>
            ) : (
              <div className="py-2">
                {filteredPractices.map((practice) => {
                  const isSelected = selectedPractices.includes(practice.practice_location);
                  const isDisabled = !isSelected && !canSelectMore;

                  return (
                    <button
                      key={practice.practice_location}
                      onClick={() => !isDisabled && togglePractice(practice.practice_location)}
                      disabled={isDisabled}
                      className={`w-full px-4 py-3 text-left flex items-center justify-between transition-colors ${
                        isDisabled
                          ? 'opacity-50 cursor-not-allowed'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer'
                      } ${isSelected ? 'bg-sky-50 dark:bg-sky-900/20' : ''}`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {practice.practice_location}
                        </div>
                        {practice.total_production && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            ${practice.total_production.toLocaleString()} production
                          </div>
                        )}
                      </div>

                      {isSelected && (
                        <CheckIcon className="w-5 h-5 text-sky-600 dark:text-sky-400 flex-shrink-0 ml-2" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          {!canSelectMore && (
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 text-center">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Maximum {maxSelect} practices can be selected
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
