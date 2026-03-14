<script setup>
const probs = defineProps({
    champions: Array[Object]
})

const emit = defineEmits(['select-champion'])
</script>


