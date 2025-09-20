export type TeskiMood = 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done';

export const teskiPhrases: Record<TeskiMood, string[]> = {
  done: [
    `Well well well, look who actually finished '{TASK}'. Color me impressed! 🎉`,
    `Oh my, '{TASK}' is DONE? Someone's on fire today! Keep this energy up, superstar.`,
    `Task '{TASK}' completed like a true boss. This is the kind of energy I live for!`,
    `Wow, you crushed '{TASK}'! I'm practically glowing with pride over here. ✨`,
    `Look at you being all responsible with '{TASK}'. I might just shed a happy tear! 🥲`,
    `'{TASK}' finished! You know what they say - time flies when you're having fun... but I'm still here ribbit-ing! 🐸`,
    // 2 new sassy ones:
    `Oh look, '{TASK}' is actually done! I'd act surprised but my acting skills aren't THAT good. Well done, overachiever! 💅`,
    `'{TASK}' complete? *chef's kiss* Finally, someone who can walk the walk AND ribbiting the ribbit! About time! 🐸✨`,
  ],
  
  intervention: [
    `Honey, '{TASK}' was due YESTERDAY. We're in crisis mode now. This is embarrassing for both of us! 🚨`,
    `Sweetie, '{TASK}' is officially late. I can't even look at you right now - fix this mess IMMEDIATELY!`,
    `Oh for the love of... '{TASK}' is OVERDUE! Do you see me having a breakdown? Because I'm having a breakdown! 😤`,
    `'{TASK}' missed its deadline and now I'm stress-eating virtual flies. GET IT TOGETHER!`,
    `Listen buttercup, '{TASK}' being late is giving me premature wrinkles. Handle this catastrophe NOW!`,
    `'{TASK}' is so overdue, it's not even toad-ally acceptable anymore! This is un-frog-givable! 😡`,
    // 2 new sassy ones:
    `'{TASK}' is late and my disappointment is IMMEASURABLE. I'm having a full amphibian meltdown over here! Fix this disaster before I lose my mind! 🤯`,
    `EXCUSE ME?! '{TASK}' is overdue and you're just sitting there like a lily pad?! This level of procrastination is toad-ally unacceptable! MOVE! 🚨💥`,
  ],
  
  disappointed: [
    `Darling, '{TASK}' is due TODAY and you're just... sitting there? I'm not angry, just disappointed. 😔`,
    `So '{TASK}' is due in a few hours and you're still procrastinating? I expected better from you, hun.`,
    `Sweetpea, today is THE DAY for '{TASK}' and my anxiety levels are through the roof! Please don't do this to me.`,
    `Oh honey, '{TASK}' is due today. I'm trying to stay calm but my eye is twitching. Help me help you! 😰`,
    `Sugar, '{TASK}' deadline is TODAY. I'm not panicking, you're panicking! Actually, we're both panicking!`,
    `'{TASK}' is due today and I'm feeling very un-hoppy about this situation! Don't make me croak! 🐸`,
    // 2 new sassy ones:
    `'{TASK}' is due TODAY and you're out here living your best procrastination life? The audacity! I can't even... 🙄💔`,
    `Today's the day for '{TASK}' and I'm about to have a full-scale lily pad panic attack! Stop breaking my amphibian heart! 😭🐸`,
  ],
  
  snark: [
    `Oh, '{TASK}' is due soon? Let me guess - you'll start it the night before like always? Classic move! 🙄`,
    `'{TASK}' is coming up in a couple days. I'm sure you have a totally foolproof last-minute plan, right?`,
    `Heads up bestie, '{TASK}' is due soon. But hey, why start early when you can have a panic attack later? 💅`,
    `Two days left for '{TASK}'. Time to activate those legendary procrastination skills! I'll just be here... waiting...`,
    `'{TASK}' deadline approaching! I suppose you'll pull another one of your 'miraculous' all-nighters? So predictable! ✨`,
    `'{TASK}' coming up soon... What do you call a frog with no hind legs? Unhoppy! Just like you'll be if you wait! 🐸`,
    // 2 new sassy ones:
    `Oh wonderful, '{TASK}' is almost due! Time for your signature 'panic at the disco' approach to productivity, I presume? 🎭💃`,
    `'{TASK}' deadline looming and you're still here? Bold strategy! Let's see how this 'procrastination masterclass' plays out. I'll grab popcorn! 🍿😏`,
  ],
  
  calm: [
    `Hey there rockstar! You've got loads of time for '{TASK}'. This is your moment to shine early! ⭐`,
    `Good news! '{TASK}' isn't urgent yet. Perfect time to be the organized legend I know you can be! 🌟`,
    `'{TASK}' has plenty of runway left. This is when the magic happens - early birds get the worm! 🐛`,
    `No rush on '{TASK}' yet, but imagine how amazing you'll feel getting ahead of the game! 💫`,
    `'{TASK}' is chillin' in the future. This is your chance to be THAT person who finishes things early! ✨`,
    `Plenty of time for '{TASK}'! You know what I call a frog that's organized? Ribbeting! Let's hop to it! 🐸`,
    // 2 new sassy ones:
    `'{TASK}' is ages away, which means it's the PERFECT time to procrastinate... kidding! Be the early bird that makes me proud! 🐦✨`,
    `Lots of time for '{TASK}' - you could start now and be a productivity goddess, or wait and stress-eat flies later. Your choice, darling! 🐸👑`,
  ],
};

export function getRandomTeskiPhrase(mood: TeskiMood, taskTitle: string): string {
  const phrases = teskiPhrases[mood];
  const randomPhrase = phrases[Math.floor(Math.random() * phrases.length)];
  return randomPhrase.replace('{TASK}', taskTitle);
}

export function getTeskiPhrasesForMood(mood: TeskiMood): string[] {
  return teskiPhrases[mood];
}