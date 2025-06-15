import './LoadingSpinner.css';

function LoadingSpinner() {
  return (
    <div className="loading">
      <div className="loading-spinner"></div>
      <span>Finding the best developer matches...</span>
    </div>
  );
}

export default LoadingSpinner;