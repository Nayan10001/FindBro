import './TagList.css';

function TagList({ items, tagClass, emptyText }) {
  if (!items || items.length === 0) {
    return (
      <div className="tag-list">
        <span className="empty-text">{emptyText}</span>
      </div>
    );
  }

  return (
    <div className="tag-list">
      {items.map((item, index) => (
        <span key={index} className={`tag ${tagClass}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

export default TagList;