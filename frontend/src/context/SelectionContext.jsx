import { createContext, useContext, useEffect, useState } from 'react'

const KEY = 'ist_selection'
const SelectionContext = createContext(null)

export function SelectionProvider({ children }) {
  const [selection, setSelectionState] = useState(null)

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(KEY)
      if (raw) setSelectionState(JSON.parse(raw))
    } catch {
      /* ignore */
    }
  }, [])

  function setSelection(next) {
    setSelectionState(next)
    if (next) sessionStorage.setItem(KEY, JSON.stringify(next))
    else sessionStorage.removeItem(KEY)
  }

  function clearSelection() {
    setSelection(null)
  }

  return (
    <SelectionContext.Provider value={{ selection, setSelection, clearSelection }}>
      {children}
    </SelectionContext.Provider>
  )
}

export function useSelection() {
  const ctx = useContext(SelectionContext)
  if (!ctx) throw new Error('useSelection must be used within SelectionProvider')
  return ctx
}
