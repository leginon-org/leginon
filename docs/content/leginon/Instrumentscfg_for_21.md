-   One computer for both tem and digital camera:
        [tem]
        class: tecnai.Tecnai
        [camera]
        class: gatan.Gatan


-   Sperate computers for the two instrument: configure only the instrument reside on the particular computer
    -   On the computer that controls the tem:
            [tem]
            class: tecnai.Tecnai
    -   On the computer that controls the digital camera:
            [camera]
            class: gatan.Gatan
