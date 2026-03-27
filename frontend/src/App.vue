<script setup>
import { ref, onMounted, computed, watch } from "vue";
import axios from "axios";
import TeamDraft from "./components/TeamDraft.vue";

const roleIcons = {
  all: new URL ('./assets/all.png', import.meta.url).href, 
  top: new URL ('./assets/top.svg', import.meta.url).href,
  jungle: new URL ('./assets/jungle.svg', import.meta.url).href,
  middle: new URL ('./assets/middle.svg', import.meta.url).href,  
  bottom: new URL ('./assets/bottom.svg', import.meta.url).href,
  support: new URL ('./assets/support.svg', import.meta.url).href
}


const myTeam = ref([null, null, null, null, null]);
const enemyTeam = ref([null, null, null, null, null]);
const allChampions = ref([]);
const searchQuery = ref("");   
const activeSlot = ref(null); 
const ROLE_NAMES = ["Top", "Jungle", "Middle", "Bottom", "Support"];
const selectedRole = ref("all")
const draggedSlot = ref(null);
const delta = ref(false)


onMounted(async () => {
  try {
    const version_response = await axios.get("https://ddragon.leagueoflegends.com/realms/euw.json")
    const version_data = version_response.data
    const version = version_data.v
    console.log(version)  

    const champs_response = await axios.get(`https://ddragon.leagueoflegends.com/cdn/${version}/data/de_DE/champion.json`);
    const champ_data = champs_response.data.data;


    const roles_response = await axios.get("http://127.0.0.1:5000/api/get-champ-roles")
    const roles_data = roles_response.data

    allChampions.value = Object.values(champ_data).map(champ => {
      const normName = normalize(champ.name);
      return{
        name: champ.name,
        id: champ.id,
        normalizedName: normName,
        imageUrl: `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${champ.image.full}`,
        score: null,
        roles: roles_data[normName] || []
      };
    });  

    console.log(allChampions.value)
  } catch (error) {
    console.error("Konnte Champions nicht laden:", error);
  }



});

const fetchRecommendations = async () => {
  try {
    const formatPicks = (teamArray) => {
      let formattedTeam = {};
      teamArray.forEach((champ, index) => {
        const role = ROLE_NAMES[index].toLowerCase();
        formattedTeam[role] = champ ? champ.normalizedName : null;
      });
      return formattedTeam;
    };

    const currentRole = activeSlot.value !== null 
    ? ROLE_NAMES[activeSlot.value.index].toLowerCase()
    : "All";

    const isTeamSide = activeSlot.value.side === 'team';


    const payload = {
      role: currentRole,
      team_picks: isTeamSide ? formatPicks(myTeam.value) : formatPicks(enemyTeam.value),
      enemy_picks: isTeamSide ? formatPicks(enemyTeam.value) : formatPicks(myTeam.value),
      delta: delta.value
    };
  

    console.log("Sende an Backend:", payload);

    const response = await axios.post("http://127.0.0.1:5000/api/get-recommendation", payload);
    console.log(response)

    const newScores = response.data.recommendations; 

    if (newScores) {
      allChampions.value.forEach(champ => {
        const score = newScores[champ.normalizedName];
        champ.score = score !== undefined ? score : null;
      });
    }
  } catch (error) {
    console.error("Fehler:", error);
  }
};

const handleSlotClick = (index, side) => {
  activeSlot.value = { index, side };
  fetchRecommendations();
};

const selectChampion = (champ) => {
  if (!activeSlot.value || isPicked(champ)) return;

  const { index, side } = activeSlot.value;
  if (side === 'team') {
    myTeam.value[index] = champ;
  } else {
    enemyTeam.value[index] = champ;
  }
  
  searchQuery.value = "";
};

const recommendedChamps = computed(() => {
  let list = [...allChampions.value];

  if (selectedRole.value !== "all") {
    list = list.filter(c => c.roles.includes(selectedRole.value));
  }

  if (searchQuery.value) {
    list = list.filter(c => 
      c.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
  }
  return list.sort((a, b) => {
    if (a.score === null && b.score === null) return 0;
    
    if (a.score === null) return 1;
    
    if (b.score === null) return -1;
    
    return b.score - a.score;
  }); 
});

const isPicked = (champ) => {
  const inMyTeam = myTeam.value.some(p => p?.id === champ.id);
  const inEnemyTeam = enemyTeam.value.some(p => p?.id === champ.id);
  
  return inMyTeam || inEnemyTeam;
};  

const removeChampion = (index, side) => {
  if (side === 'team'){
    myTeam.value[index] = null
  }
  else {
    enemyTeam.value[index] = null
  }
  fetchRecommendations()
}

const normalize = (name) => {
  const baseName = name.toLowerCase().replace(/(\s|\W)/g, "");
  
  const aliases = {
    "wukong": "monkeyking",
  };

  return aliases[baseName] || baseName;
};

const handleDragStart = (index, side) => {
  draggedSlot.value = { index, side };
};

const handleDrop = (targetIndex, targetSide) => {
  if (!draggedSlot.value) return;

  const { index: sourceIndex, side: sourceSide } = draggedSlot.value;

  if (sourceSide === targetSide && sourceIndex !== targetIndex) {
    const team = sourceSide === 'team' ? myTeam : enemyTeam;
    
    const temp = team.value[sourceIndex];
    team.value[sourceIndex] = team.value[targetIndex];
    team.value[targetIndex] = temp;

    fetchRecommendations(); 
  }

  draggedSlot.value = null;
};

const handleDeltaClick = () => {

  delta.value = !delta.value; 
  fetchRecommendations()
}


</script>

<template>
  <div class="min-h-screen bg-slate-950 text-white p-6 flex justify-between gap-8">
    
    <TeamDraft 
      title="Your Team" 
      :picks="myTeam" 
      :is-enemy="false" 
      :active-index="activeSlot?.side === 'team' ? activeSlot.index : null" 
      @select-slot="(idx) => handleSlotClick(idx, 'team')"
      @remove-slot="(idx) => removeChampion(idx, 'team')"
      @drag-start="(idx) => handleDragStart(idx, 'team')" 
      @drop-slot="(idx) => handleDrop(idx, 'team')"
    />

    <div class="flex-1 flex flex-col items-center border-x border-slate-800 px-8">
      <h1 class="text-3xl font-black mb-6 text-teal-500 italic uppercase">Optimal Pick</h1>
      
      <input 
        v-model="searchQuery"
        placeholder="Champion suchen..."
        class="w-full max-w-md bg-slate-900 border border-slate-700 p-3 rounded-lg mb-8 focus:ring-2 focus:ring-teal-500 outline-none"
      />

      <div class="flex gap-2 mb-4 justify-center">
        <button 
          v-for="role in ['all', 'top', 'jungle', 'middle', 'bottom', 'support']" 
          :key="role"
          @click="selectedRole = role"
          class="px-3 py-1 rounded text-xs uppercase font-bold transition-all"
          :class="selectedRole === role ? 'bg-teal-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'"
        >
        <img 
          :src="roleIcons[role]" 
          :alt="role"
          class="w-6 h-6 object-contain"
        /> 
        </button>

        <div class="w-px h-8 bg-slate-700 mx-1"></div>

          <button 
            @click="handleDeltaClick"
            class="px-4 py-2 rounded text-[10px] font-bold uppercase tracking-widest transition-all duration-300 border h-8.5 bg-slate-800 border-slate-700 text-white hover:border-teal-500"
          >
            {{ delta ? 'Delta' : 'Winrate' }}
          </button>
    </div>

      <div class="grid grid-cols-4 lg:grid-cols-6 gap-4 overflow-y-auto max-h-[70vh] p-2">
        <div 
          v-for="champ in recommendedChamps" 
          :key="champ.id"
          @click="selectChampion(champ)"
          class="cursor-pointer group flex flex-col items-center"
          :class="{ 'opacity-20 grayscale pointer-events-none': isPicked(champ)}"
        >
          <div class="relative w-20 h-20 border-2 border-slate-800 group-hover:border-teal-400 transition-all">
            <img :src="champ.imageUrl" class="w-full h-full object-cover" />
            <div 
              v-if="champ.score !== null"
              class="absolute -bottom-2 -right-2 bg-teal-600 text-[10px] px-1.5 py-0.5 rounded font-bold shadow-lg">
              {{champ.score}}{{!delta ? '%' : '' }}
            </div>
          </div>
          <span class="text-[11px] mt-2 text-slate-400 group-hover:text-white">{{ champ.name }}</span>
        </div>
      </div>
    </div>

    <TeamDraft 
      title="Enemy Team" 
      :picks="enemyTeam" 
      :is-enemy="true" 
      :active-index="activeSlot?.side === 'enemy' ? activeSlot.index : null"
      @select-slot="(idx) => handleSlotClick(idx, 'enemy')"
      @remove-slot="(idx) => removeChampion(idx, 'enemy')"
      @drag-start="(idx) => handleDragStart(idx, 'enemy')"
      @drop-slot="(idx) => handleDrop(idx, 'enemy')"
    />

  </div>
</template>