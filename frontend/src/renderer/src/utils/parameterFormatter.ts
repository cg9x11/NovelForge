
export interface ParameterFormatOptions {
  type: string
  value: any
}

export class ParameterFormatter {
  private static escapeString(value: any): string {
    const text = String(value)
    return text
      .replace(/\\/g, '\\\\')
      .replace(/\r/g, '\\r')
      .replace(/\n/g, '\\n')
      .replace(/\t/g, '\\t')
      .replace(/"/g, '\\"')
  }
  static isVariableReference(value: any): boolean {
    if (value === null || value === undefined) return false
    const strValue = String(value)
    return /^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$/.test(strValue)
  }

  static isEmpty(value: any): boolean {
    if (value === 0 || value === false) return false
    if (value === null || value === undefined) return true

    const strValue = String(value).trim()
    return strValue === ''
  }

  static format(options: ParameterFormatOptions): string {
    const { type, value } = options

    if (this.isEmpty(value)) {
      return ''
    }

    if (this.isVariableReference(value)) {
      return String(value)
    }

    let result: string
    switch (type) {
      case 'integer':
      case 'number':
        result = String(value)
        break

      case 'boolean':
        result = (value === 'true' || value === true) ? 'True' : 'False'
        break

      case 'string':
        result = `"${this.escapeString(value)}"`
        break

      case 'array':
        if (Array.isArray(value)) {
          const items = value.map(item => `"${this.escapeString(item)}"`)
          result = `[${items.join(', ')}]`
        } else if (typeof value === 'string') {
          const items = value.split(',').map(item => item.trim()).filter(item => item)
          result = `[${items.map(item => `"${this.escapeString(item)}"`).join(', ')}]`
        } else {
          result = this.formatComplexType(value)
        }
        break

      case 'object':
        result = this.formatComplexType(value)
        break

      default:
        if (typeof value === 'object' && value !== null) {
          result = this.formatComplexType(value)
        } else {
          result = `"${this.escapeString(value)}"`
        }
        break
    }

    if (typeof result !== 'string') {
      result = JSON.stringify(result)
    }

    return result
  }

  private static formatComplexType(value: any): string {
    if (Array.isArray(value)) {
      const items = value.map(item => {
        if (typeof item === 'object' && item !== null) {
          return this.formatComplexType(item)
        } else if (typeof item === 'string') {
          return `"${this.escapeString(item)}"`
        } else if (typeof item === 'number') {
          return String(item)
        } else if (typeof item === 'boolean') {
          return item ? 'True' : 'False'
        } else {
          return `"${this.escapeString(item)}"`
        }
      })
      return `[${items.join(', ')}]`
    }

    if (typeof value === 'object' && value !== null) {
      const pairs = Object.entries(value).map(([key, val]) => {
        let formattedVal: string
        if (typeof val === 'object' && val !== null) {
          formattedVal = this.formatComplexType(val)
        } else if (typeof val === 'string') {
          formattedVal = `"${this.escapeString(val)}"`
        } else if (typeof val === 'number') {
          formattedVal = String(val)
        } else if (typeof val === 'boolean') {
          formattedVal = val ? 'True' : 'False'
        } else {
          formattedVal = `"${this.escapeString(val)}"`
        }
        return `"${key}": ${formattedVal}`
      })
      return `{${pairs.join(', ')}}`
    }

    return String(value)
  }

  static parseDisplayValue(value: any): string {
    if (value === null || value === undefined) return ''

    if (typeof value === 'object' && !Array.isArray(value)) {
      try {
        return this.formatComplexType(value)
      } catch (e) {
        return JSON.stringify(value)
      }
    }

    if (Array.isArray(value)) {
      try {
        return this.formatComplexType(value)
      } catch (e) {
        return JSON.stringify(value)
      }
    }

    let strValue = String(value)

    if ((strValue.startsWith('"') && strValue.endsWith('"')) ||
        (strValue.startsWith("'") && strValue.endsWith("'"))) {
      return strValue.substring(1, strValue.length - 1)
    }

    return strValue
  }
}
