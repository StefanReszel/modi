$(function(){
    closingMessage();
    
    
    function closingMessage(){
        let message = $('.message');

        message.click(function(event){
            event.preventDefault();
            $(this).slideUp();
        });
    }
});
