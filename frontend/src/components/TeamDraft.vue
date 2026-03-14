<script setup> 
import DraftSlot from './DraftSlot.vue';

const props = defineProps({
    picks: Array,
    isEnemy: Boolean,
    title: String,
    activeIndex: Number
})

const emit = defineEmits(['select-slot', 'remove-slot', 'drag-start', 'drop-slot']);
</script>

<template>
    <div class="flex flex-col items-center bg-gray-900 p-4 rounded-lg">
        <h2 class="text-white font-bold mb-4">{{ title }}</h2>
        
        <DraftSlot 
            v-for="(pick, index) in picks"
            :key="index"
            :champion="pick"
            :is-enemy="isEnemy"
            :is-active="index === activeIndex"
            :role-label="['Top', 'Jungle', 'Middle', 'Bottom', 'Support'][index]"
            @select="$emit('select-slot', index)"
            @remove="$emit('remove-slot', index)"
            @drag-start="$emit('drag-start', index)"
            @drop-slot="$emit('drop-slot', index)"
        />
    </div>
</template>