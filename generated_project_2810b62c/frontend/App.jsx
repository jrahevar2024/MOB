```javascript
import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8001';

// Reusable Loading Spinner Component
const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-4">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);

// Reusable Error Alert Component
const ErrorAlert = ({ message, onDismiss }) => (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
    <span className="block sm:inline">{message}</span>
    {onDismiss && (
      <button
        onClick={onDismiss}
        className="absolute top-0 bottom-0 right-0 px-4 py-3 text-red-700 hover:text-red-900 focus:outline-none focus:ring-2 focus:ring-red-500"
        aria-label="Dismiss error"
      >
        &times;
      </button>
    )}
  </div>
);

// Reusable Success Notification Component
const SuccessNotification = ({ message, onDismiss }) => (
  <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
    <span className="block sm:inline">{message}</span>
    {onDismiss && (
      <button
        onClick={onDismiss}
        className="absolute top-0 bottom-0 right-0 px-4 py-3 text-green-700 hover:text-green-900 focus:outline-none focus:ring-2 focus:ring-green-500"
        aria-label="Dismiss success"
      >
        &times;
      </button>
    )}
  </div>
);

// Reusable Confirmation Dialog Component
const ConfirmationDialog = ({ message, onConfirm, onCancel, isOpen }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex justify-center items-center z-50">
      <div className="relative p-5 border w-96 shadow-lg rounded-md bg-white">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Confirm Action</h3>
        <p className="text-gray-700 mb-6">{message}</p>
        <div className="flex justify-end space-x-4">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 transition duration-150 ease-in-out"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition duration-150 ease-in-out"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
};

// Reusable Empty State Component
const EmptyState = ({ message, onAction, actionText }) => (
  <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg shadow-sm text-gray-600">
    <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
    </svg>
    <p className="text-lg font-medium mb-4">{message}</p>
    {onAction && actionText && (
      <button
        onClick={onAction}
        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150 ease-in-out"
      >
        {actionText}
      </button>
    )}
  </div>
);

// Resource Form Component (for Create and Edit)
const ResourceForm = ({ initialData, onSubmit, onCancel, isLoading, submitButtonText }) => {
  const [formData, setFormData] = useState(initialData || { name: '', description: '' });
  const [formErrors, setFormErrors] = useState({});

  useEffect(() => {
    setFormData(initialData || { name: '', description: '' });
    setFormErrors({}); // Clear errors when initialData changes (e.g., switching from create to edit)
  }, [initialData]);

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setFormErrors((prev) => ({ ...prev, [name]: undefined })); // Clear error for field on change
  }, []);

  const validateForm = useCallback(() => {
    const errors = {};
    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }
    if (!formData.description.trim()) {
      errors.description = 'Description is required';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  }, [formData, onSubmit, validateForm]);

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md max-w-md mx-auto">
      <div className="mb-4">
        <label htmlFor="name" className="block text-gray-700 text-sm font-bold mb-2">
          Name:
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 ${formErrors.name ? 'border-red-500' : ''}`}
          disabled={isLoading}
        />
        {formErrors.name && <p className="text-red-500 text-xs italic mt-1">{formErrors.name}</p>}
      </div>
      <div className="mb-6">
        <label htmlFor="description" className="block text-gray-700 text-sm font-bold mb-2">
          Description:
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="4"
          className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 ${formErrors.description ? 'border-red-500' : ''}`}
          disabled={isLoading}
        ></textarea>
        {formErrors.description && <p className="text-red-500 text-xs italic mt-1">{formErrors.description}</p>}
      </div>
      <div className="flex items-center justify-between">
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? 'Submitting...' : submitButtonText}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-gray-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          Cancel
        </button>
      </div>
    </form>
  );
};


// Main App Component
function App() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const [view, setView] = useState('list'); // 'list', 'create', 'details', 'edit'
  const [selectedResourceId, setSelectedResourceId] = useState(null);
  const [resourceToDelete, setResourceToDelete] = useState(null); // For confirmation dialog

  // --- API Call Pattern Helper ---
  const apiCall = useCallback(async (url, options = {}) => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null); // Clear previous success messages
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        // Attempt to parse error message from response body
        let errorMessage = `Server error: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.error || errorMessage;
        } catch (jsonError) {
          // If JSON parsing fails, use default message
        }
        throw new Error(errorMessage);
      }
      // For DELETE requests, response might be empty or just a status
      if (options.method === 'DELETE' || response.status === 204) {
        return {}; // Return empty object for successful deletion
      }
      return await response.json();
    } catch (err) {
      setError(err.message || 'Failed to perform action due to network error.');
      throw err; // Re-throw to allow specific error handling in caller if needed
    } finally {
      setLoading(false);
    }
  }, []);

  // --- CRUD Operations ---

  // GET /resources
  const fetchResources = useCallback(async () => {
    try {
      const data = await apiCall(`${API_BASE_URL}/resources`);
      setResources(data);
    } catch (err) {
      // Error already set by apiCall
    }
  }, [apiCall]);

  // GET /resources/{id} (used internally for details/edit views)
  const fetchResourceDetails = useCallback(async (id) => {
    try {
      const data = await apiCall(`${API_BASE_URL}/resources/${id}`);
      return data;
    } catch (err) {
      // Error already set by apiCall
      return null;
    }
  }, [apiCall]);

  // POST /resources
  const createResource = useCallback(async (newResource) => {
    try {
      const data = await apiCall(`${API_BASE_URL}/resources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newResource),
      });
      setResources((prev) => [...prev, data]); // Optimistic update
      setSuccessMessage('Resource created successfully!');
      setView('list'); // Go back to list view
    } catch (err) {
      // Error already set by apiCall
    }
  }, [apiCall]);

  // PUT /resources/{id}
  const updateResource = useCallback(async (id, updatedResource) => {
    try {
      const data = await apiCall(`${API_BASE_URL}/resources/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedResource),
      });
      setResources((prev) => prev.map((res) => (res.id === id ? data : res))); // Optimistic update
      setSuccessMessage('Resource updated successfully!');
      setView('list'); //