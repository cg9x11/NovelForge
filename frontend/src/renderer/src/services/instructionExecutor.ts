
import { set, get } from 'lodash-es'
import type { Instruction } from '@renderer/types/instruction'

export class InstructionExecutor {
  private data: Record<string, any> = {}

  constructor(initialData: Record<string, any> = {}) {
    this.data = { ...initialData }
  }

  execute(instruction: Instruction): void {
    switch (instruction.op) {
      case 'set':
        this.executeSet(instruction.path, instruction.value)
        break
      case 'append':
        this.executeAppend(instruction.path, instruction.value)
        break
      case 'done':
        break
    }
  }

  private executeSet(path: string, value: any): void {
    const lodashPath = this.convertPath(path)
    set(this.data, lodashPath, value)
  }

  private executeAppend(path: string, value: any): void {
    const lodashPath = this.convertPath(path)
    const arr = get(this.data, lodashPath) || []

    if (!Array.isArray(arr)) {
      return
    }

    arr.push(value)
    set(this.data, lodashPath, arr)
  }

  private convertPath(pointer: string): string {
    if (pointer.startsWith('/')) {
      pointer = pointer.slice(1)
    }

    return pointer.replace(/\//g, '.')
  }

  getData(): Record<string, any> {
    return this.data
  }

  reset(newData: Record<string, any> = {}): void {
    this.data = { ...newData }
  }

  clear(): void {
    this.data = {}
  }
}
