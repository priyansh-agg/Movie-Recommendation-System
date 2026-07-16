import { type ReactNode, type ChangeEvent } from 'react';
import './Input.css';

interface InputProps {
  label?: string;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  icon?: ReactNode;
  error?: string;
  name?: string;
  autoComplete?: string;
}

export default function Input({
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  icon,
  error,
  name,
  autoComplete,
}: InputProps) {
  return (
    <div className={`input-field ${error ? 'input-field--error' : ''}`}>
      {label && <label className="input-field__label">{label}</label>}
      <div className="input-field__wrapper">
        {icon && <span className="input-field__icon">{icon}</span>}
        <input
          type={type}
          className="input-field__input"
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          name={name}
          autoComplete={autoComplete}
          spellCheck={false}
        />
      </div>
      {error && <p className="input-field__error">{error}</p>}
    </div>
  );
}
