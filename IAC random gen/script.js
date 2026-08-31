/* =========================================
   PROMPT BATTLE TEAM GENERATOR
   Numbers: 1 - 150
   Team Size: 3
========================================= */


const TOTAL_NUMBERS = 116;
const TEAM_SIZE = 3;


// HTML Elements
const numberElements = [
    document.getElementById("number1"),
    document.getElementById("number2"),
    document.getElementById("number3")
];

const boxes = [
    document.getElementById("box1"),
    document.getElementById("box2"),
    document.getElementById("box3")
];

const generateBtn = document.getElementById("generateBtn");
const buttonText = document.getElementById("buttonText");

const battleMessage = document.getElementById("battleMessage");

const usedCountElement = document.getElementById("usedCount");
const progressFill = document.getElementById("progressFill");

const resetBtn = document.getElementById("resetBtn");

const celebration = document.getElementById("celebration");


// =========================================
// STORAGE
// =========================================

let usedNumbers =
    JSON.parse(localStorage.getItem("promptBattleUsedNumbers")) || [];


// =========================================
// INITIALIZE
// =========================================

updateProgress();


// =========================================
// GET AVAILABLE NUMBERS
// =========================================

function getAvailableNumbers() {

    const available = [];

    for (let i = 1; i <= TOTAL_NUMBERS; i++) {

        if (!usedNumbers.includes(i)) {
            available.push(i);
        }

    }

    return available;
}


// =========================================
// RANDOM NUMBER
// =========================================

function getRandomNumber(array) {

    const index =
        Math.floor(Math.random() * array.length);

    return array[index];
}


// =========================================
// GENERATE TEAM
// =========================================

async function generateTeam() {

    const availableNumbers = getAvailableNumbers();


    // Check if enough numbers remain
    if (availableNumbers.length < TEAM_SIZE) {

        battleMessage.textContent =
            "⚠ ALL NUMBERS HAVE BEEN ASSIGNED!";

        generateBtn.disabled = true;

        buttonText.textContent = "NO NUMBERS LEFT";

        return;
    }


    // Disable button while generating
    generateBtn.disabled = true;

    buttonText.textContent = "GENERATING...";

    battleMessage.textContent =
        "⚡ SCANNING FOR YOUR TEAM...";


    // Remove old active state
    boxes.forEach(box => {
        box.classList.remove("active");
    });


    // Reset numbers
    numberElements.forEach(element => {
        element.textContent = "--";
    });


    /*
        Select 3 unique numbers.

        We remove each selected number from
        the temporary available array so
        duplicates are impossible.
    */

    const selectedNumbers = [];

    const tempNumbers = [...availableNumbers];


    for (let i = 0; i < TEAM_SIZE; i++) {

        const randomIndex =
            Math.floor(Math.random() * tempNumbers.length);

        const selected =
            tempNumbers.splice(randomIndex, 1)[0];

        selectedNumbers.push(selected);
    }


    // Dramatic number reveal
    for (let i = 0; i < TEAM_SIZE; i++) {

        await revealNumber(
            numberElements[i],
            boxes[i],
            selectedNumbers[i],
            i
        );

    }


    // Add selected numbers permanently
    usedNumbers.push(...selectedNumbers);

    saveNumbers();

    updateProgress();


    // Final message
    battleMessage.textContent =
        "🔥 YOUR TEAM IS LOCKED!";


    buttonText.textContent =
        "GENERATE NEXT TEAM";


    generateBtn.disabled = false;


    // Celebration popup
    showCelebration();

}


// =========================================
// REVEAL NUMBER
// =========================================

function revealNumber(
    element,
    box,
    finalNumber,
    position
) {

    return new Promise(resolve => {

        let counter = 0;

        const duration = 850;

        const intervalTime = 45;

        const steps =
            Math.floor(duration / intervalTime);


        box.classList.add("active");

        box.classList.remove("reveal");

        void box.offsetWidth;

        box.classList.add("reveal");


        const interval = setInterval(() => {

            counter++;


            /*
                Show random numbers during
                the hacking / scanning effect.
            */

            const randomDisplay =
                Math.floor(Math.random() * 116) + 1;


            element.textContent =
                String(randomDisplay).padStart(3, "0");


            if (counter >= steps) {

                clearInterval(interval);


                // Show final number
                element.textContent =
                    String(finalNumber).padStart(3, "0");


                box.querySelector(
                    ".number-status"
                ).textContent = "SELECTED";


                resolve();

            }

        }, intervalTime);

    });

}


// =========================================
// CELEBRATION
// =========================================

function showCelebration() {

    celebration.classList.add("show");


    setTimeout(() => {

        celebration.classList.remove("show");

    }, 1800);

}


// =========================================
// UPDATE PROGRESS
// =========================================

function updateProgress() {

    const used =
        usedNumbers.length;


    usedCountElement.textContent =
        used;


    const percentage =
        (used / TOTAL_NUMBERS) * 100;


    progressFill.style.width =
        `${percentage}%`;


    // If all numbers are used
    if (used >= TOTAL_NUMBERS) {

        battleMessage.textContent =
            "🏆 ALL PLAYERS HAVE BEEN ASSIGNED!";

        buttonText.textContent =
            "BATTLE COMPLETE";

        generateBtn.disabled = true;
    }

}


// =========================================
// SAVE NUMBERS
// =========================================

function saveNumbers() {

    localStorage.setItem(
        "promptBattleUsedNumbers",
        JSON.stringify(usedNumbers)
    );

}


// =========================================
// RESET
// =========================================

function resetNumbers() {

    const confirmation =
        confirm(
            "Reset all assigned numbers?\n\nThis will make all 116 numbers available again."
        );


    if (!confirmation) {
        return;
    }


    usedNumbers = [];


    localStorage.removeItem(
        "promptBattleUsedNumbers"
    );


    // Reset UI
    numberElements.forEach(element => {

        element.textContent = "--";

    });


    boxes.forEach(box => {

        box.classList.remove("active");
        box.classList.remove("reveal");

        box.querySelector(
            ".number-status"
        ).textContent = "WAITING";

    });


    battleMessage.textContent =
        "READY FOR BATTLE?";


    buttonText.textContent =
        "GENERATE TEAM";


    generateBtn.disabled = false;


    updateProgress();

}


// =========================================
// EVENT LISTENERS
// =========================================

generateBtn.addEventListener(
    "click",
    generateTeam
);


resetBtn.addEventListener(
    "click",
    resetNumbers
);


// =========================================
// KEYBOARD SHORTCUT
// SPACE = GENERATE
// =========================================

document.addEventListener(
    "keydown",
    event => {

        if (
            event.code === "Space" &&
            !generateBtn.disabled
        ) {

            event.preventDefault();

            generateTeam();

        }

    }
);
