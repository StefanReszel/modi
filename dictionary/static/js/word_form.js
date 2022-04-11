$(function(){
    // setting submitting by clicking enter
    $('#id_definition').keydown((event) => {
        if (event.key == 'Enter'){
            $('#add_word').click();
        }
    });
    
    // deleting word with AJAX
    let csrfToken = Cookies.get('csrftoken');

    $('#words').click((event) => {
        if (event.target.classList.contains("delete")){
            event.preventDefault();
            let definition = event.target.dataset.definition;
            $.post({
                url: deleteUrl,
                data: {
                    definition: definition,
                },
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                success: () => {
                    event.target.closest(".row").remove();
                    updateCounter();
                },
            });
        }
    });

    function updateCounter(){
        let numberOfWords = $('#counter').text();
        $('#counter').text(numberOfWords - 1);
    }
});
