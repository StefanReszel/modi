$(function(){
    const dictionary = $.parseJSON($('#words').text());
    let definitions = Object.keys(dictionary);
    let definition;
    let answer;
    let isAnswerGood;
    let number;
    let prevNumber;

    // colors for input's background depending on answer
    let initialColor = '#f8f9fa'
    let correctColor = '#d1e7dd'
    let wrongColor = '#f8d7da'

    // audio references
    let pathToAudio = `${window.location.origin}/static/audio`
    let correctSound = new Audio(`${pathToAudio}/correct.mp3`);
    let wrongSound = new Audio(`${pathToAudio}/wrong.mp3`);

    
    initialize();
    pushEnterToPressButton();
    setSpeakerOptions();


    $('#sound-icon').click(()=>{utterWord(dictionary[definition]);});


    function initialize(){
        number = randNumber(definitions.length);
        prevNumber = number;
        definition = randomDefinition(number);
        
        toggleGoodAnswer(isAnswerGood);
        putDefinitionAndGoodAnswerInHtml(definition);
        resetInput();
        changeButtonValue();
        focusOnInput()

        // binding handler with event once
        $('#button').one('click', checkAnswer);
    }
    

    function checkAnswer(){
        answer = getAnswer();
        isAnswerGood = compareAnswer(definition, answer);

        changeInputColorAndProp(isAnswerGood);
        changeButtonValue();
        removeWord(isAnswerGood);
        toggleGoodAnswer(isAnswerGood);
        
        playAudio(isAnswerGood);
        setTimeout(utterWord, 300, dictionary[definition]);

        if (definitions.length == 0){
            completeLearning();
            return;
        }
        // binding handler with event once
        $('#button').one('click', initialize);
    }    
    
    
    function randNumber(max){
        let randInt = Math.floor(Math.random() * max);      
        if (max > 1){
            if (randInt == prevNumber){
                return randNumber(max);
            }
        }
        return randInt;
    }

    function randomDefinition(number){
        return definitions[number];
    }


    function putDefinitionAndGoodAnswerInHtml(definition){
        $('#definition').text(definition);
        $('#correct-answer').text(dictionary[definition]);
    }


    function getAnswer(){
        return $('#word').val().trim();
    }


    function resetInput(){
        let input = $('#word');

        input.val('');
        input.prop('disabled', false);
        input.css('background-color', initialColor);
    }


    function compareAnswer(definition, answer){
        if (answer == dictionary[definition]){
            return true;
        }
        return false;
    }


    function removeWord(correct){
        if (correct){
            definitions.splice(number, 1);
            // updating counter
            let counter = $('#counter')
            let numberOfWords = counter.text();
            counter.text(numberOfWords - 1);
        }
    }


    function toggleGoodAnswer(correct){
        if (!correct){
            $('#correct-answer-box').toggle();
        }
    }


    function changeInputColorAndProp(correct){
        let input = $('#word');

        input.prop('disabled', true);
        if (correct){
            input.css('background-color', correctColor);
        }else{
            input.css('background-color', wrongColor);
        }
    }


    function changeButtonValue(){
        let button = $('#button');
        let previousValue = button.val();

        button.val(button.data('next-value'));
        button.data('next-value', previousValue);
    }


    function completeLearning(){
        let button = $('#button');
        let link = $('#complete')[0];

        button.click(() => {link.click();});
    }


    function pushEnterToPressButton(){
        let button = $('#button');

        $(document).keydown((event) => {
            if (event.key == 'Enter'){
                button.click();
            }
        });
    }


    function focusOnInput(){
        $('#word').focus();
    }


    function playAudio(correct){
        if (correct){
            correctSound.play();
        }else{
            wrongSound.play();
        }    
    }    


    function utterWord(word){
        if (typeof speechSynthesis !== 'undefined'){
            let utterance = new SpeechSynthesisUtterance();
            let language = $('#languages').val();
            
            if (language == 'mute'){
                return;
            }
            utterance.text = word;
            utterance.lang = language;
            utterance.rate = 0.8;

            if (speechSynthesis.speaking){
                speechSynthesis.cancel();
            }
            speechSynthesis.speak(utterance);
        }
    }


    function setSpeakerOptions(){
        if (typeof speechSynthesis !== 'undefined'){
            speechSynthesis.onvoiceschanged = () => {
                let languages = {
                    'pl-PL': 'Polski',
                    'en-US': 'English(US)',
                    'en-GB': 'English(GB)',
                    'de-DE': 'Deutsch',
                    'es-ES': 'Español',
                    'fr-FR': 'Français',
                    'it-IT': 'Italiano',
                    'ru-RU': 'Русский',
                    'nl-NL': 'Dutch',
                };
                let voices = speechSynthesis.getVoices();

                let options = $('#languages');
                let option;

                for (let language in languages){
                    for (let voice of voices){
                        if (language == voice.lang){
                            option = `<option value="${voice.lang}">${languages[voice.lang]}</option>`;
                            $(option).appendTo(options); 
                            break;
                        }
                    }
                }
                options.toggle();
            }
        }
    }
});
