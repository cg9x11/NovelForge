import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { i18n } from '@renderer/i18n'
import type { components } from '@renderer/types/generated'
import { getProjects, createProject as apiCreateProject, updateProject as apiUpdateProject, deleteProject as apiDeleteProject } from '@renderer/api/projects'

type Project = components['schemas']['ProjectRead']
type ProjectCreate = components['schemas']['ProjectCreate']
type ProjectUpdate = components['schemas']['ProjectUpdate']

const t = i18n.global.t

export const useProjectListStore = defineStore('projectList', () => {
  // 项目列表
  const projects = ref<Project[]>([])
  const isLoading = ref(false)

  // Actions
  async function fetchProjects() {
    isLoading.value = true
    try {
      const list = await getProjects()
      projects.value = (list || []).filter(p => (p.name || '') !== '__free__')
    } catch (error) {
      console.error('获取项目列表失败:', error)
      ElMessage.error(t('project_list.messages.fetchFailed'))
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function createProject(projectData: ProjectCreate) {
    try {
      const newProject = await apiCreateProject(projectData)
      await fetchProjects()
      ElMessage.success(t('project_list.messages.created'))
      return newProject
    } catch (error) {
      ElMessage.error(t('project_list.messages.createFailed', { error }))
      throw error
    }
  }

  async function updateProject(projectId: number, projectData: ProjectUpdate) {
    try {
      await apiUpdateProject(projectId, projectData)
      ElMessage.success(t('project_list.messages.updated'))
      await fetchProjects()
    } catch (error) {
      ElMessage.error(t('project_list.messages.updateFailed', { error }))
      throw error
    }
  }

  async function deleteProject(projectId: number) {
    try {
      // 额外前端保护：阻止删除保留项目
      const proj = projects.value.find(p => p.id === projectId)
      if (proj && (proj.name || '') === '__free__') {
        ElMessage.warning(t('project_list.messages.reservedCannotDelete'))
        return
      }
      await apiDeleteProject(projectId)
      ElMessage.success(t('project_list.messages.deleted'))
      await fetchProjects()
    } catch (error) {
      ElMessage.error(t('project_list.messages.deleteFailed', { error }))
      throw error
    }
  }

  function reset() {
    projects.value = []
    isLoading.value = false
  }

  return {
    // State
    projects,
    isLoading,
    
    // Actions
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    reset
  }
}) 
