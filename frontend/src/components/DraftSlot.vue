<script setup>

import {ref} from 'vue'

const props = defineProps({
    champion: Object,
    roleLabel: String, 
    isEnemy: Boolean,
    isActive: Boolean
})

const isOver = ref(false);

const emit = defineEmits(['select', 'remove', 'drag-start', 'drop-slot']);
</script>

<template>
  <div 
    :draggable="!!champion"
    @dragstart="$emit('drag-start')"
    @dragover.prevent
    @dragenter="isOver = true"
    @dragleave="isOver = false"
    @drop="isOver = false; $emit('drop-slot')"
    @click="$emit('select')"
    class="relative w-24 h-32 bg-gray-800 border-2 flex flex-col items-center justify-between m-1 transition-all duration-200 group overflow-hidden"
    :class="[
      isActive 
        ? 'border-teal-400 ring-2 ring-teal-400/50 shadow-[0_0_15px_rgba(45,212,191,0.5)] scale-105 z-10' 
        : (isEnemy ? 'border-red-900/80' : 'border-blue-900/50'),
      
      isOver ? 'border-dashed border-teal-300 bg-gray-700 scale-95' : '',
      champion ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'
    ]"
  > 

    <div 
      v-if="champion"
      class="absolute top-1 left-1 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-20 pointer-events-none"
    >
      <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="9" cy="6" r="2" /><circle cx="15" cy="6" r="2" />
        <circle cx="9" cy="12" r="2" /><circle cx="15" cy="12" r="2" />
        <circle cx="9" cy="18" r="2" /><circle cx="15" cy="18" r="2" />
      </svg>
    </div>

    <button 
      v-if="champion"
      @click.stop="$emit('remove')"
      class="absolute -top-1 -right-1 bg-slate-700 hover:bg-red-600 text-white rounded-full w-5 h-5 text-[10px] flex items-center justify-center z-30 shadow-lg border border-white/20"
    >
      ✕
    </button>

    <div class="text-[9px] text-gray-400 uppercase pt-1 z-10 font-bold">{{ roleLabel }}</div>

    <div class="flex-1 w-full overflow-hidden flex items-center justify-center">
      <img 
        v-if="champion" 
        :src="champion.imageUrl" 
        class="w-full h-full object-cover" 
      />
      <div v-else class="text-2xl text-gray-600 font-bold">+</div>
    </div>

    <div class="text-[10px] text-white pb-1 z-10 font-medium truncate w-full text-center px-1">
      {{ champion ? champion.name : 'Pick' }}
    </div>
  </div>
</template>

<!---
<template>
  <div 
    :draggable="!!champion"
    @dragstart="$emit('drag-start')"
    @dragover.prevent
    @dragenter.prevent
    @drop="$emit('drop-slot')"
    @click="$emit('select')"
    class="relative w-24 h-32 bg-gray-800 border-2 cursor-pointer flex flex-col items-center justify-center m-1"
    :class="[
      isActive 
        ? 'border-teal-400 ring-2 ring-teal-400/50 shadow-[0_0_15px_rgba(45,212,191,0.5)] scale-105 z-10' 
        : (isEnemy ? 'border-red-900/80' : 'border-blue-900/50')
    ]"
  > 

    <button 
      v-if="champion"
      @click.stop="$emit('remove')"
      class="absolute -top-2 -right-2 bg-slate-700 hover:bg-slate-500 text-slate-300 hover:text-white rounded-full w-5 h-5 text-[10px] flex items-center justify-center z-10 shadow-lg border border-white/20"
    >
      ✕
    </button>

    <div class="text-[10px] text-gray-400 uppercase">{{ roleLabel }}</div>

    <img v-if="champion" :src="champion.imageUrl" class="w-full h-full object-cover" />
    <div v-else class="text-3xl text-gray-600 font-bold">+</div>

    <div class="text-[11px] text-white mt-1">
      {{ champion ? champion.name : 'Pick' }}
    </div>
  </div>
</template>
-->