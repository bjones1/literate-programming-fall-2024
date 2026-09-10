/* # Descent into CodeChat

   ## Code explanation

   The _while(1)_ loop is what runs the game. Each iterative run of the loop is
   a turn in the game in which there will be an _input_ of the mountains and the
   _output_ to fire at a mountains. The inputs are updated per run of the loop

   <span style="background-color: yellow">KJB</span>: I think more context about the game is necessary for the reader to
   understand the goal. Specifying that these inputs are the heights and that
   the desired output is the index of the mountain to shoot at.
   
*/

/* Code used for help:
   [GitHub Link](https://gist.github.com/kYroL01/eeb7752ae71f6ae58a095ad74e989986) */

// Just the required _includes_ for the program.
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

/* This is the _main_ included in the program. */
int main()
{
    /* These 2 _int_ statements declare the variables we are using the highest
       mountain and the current mountain */
    int highestMountain;
    int currentMountain;
    /* ## Game loop below */
    while (1) {
        /* Just saving 0 to the variables created above rather than keeping it
           blank. */
        highestMountain = 0;
        currentMountain = 0;

        /* The _for_ loop below takes in and checks the mountains' heights. */
        for (int i = 0; i < 8; i++) {
            /* The _int_ below holds the height of the mountains. */
            int mountain_height;
            /* The _scanf_ below enters the mountain numbers and heights. */
            scanf("%d", &mountain_height);
            

            /* An _if_ statement to check for and save the **largest** mountain. */
            if(mountain_height > highestMountain){
                highestMountain = mountain_height;
                currentMountain = i;

            /*
               
               <span style="background-color: yellow">KJB</span>: _currentMountain_ 
               doesn't seem to be used outside of holding _i_ which is redundant.
               the provided _mountain_height_ variable already accomplishes holding 
               the height of the mounatin in test, so no need for _currentMountain_.

            */

            } 
            /* end of if */
            
        } 
        /* end of for */
            
            /* ## Output Statement

               The statement below outputs a number which causes the ship in the
               game to shoot the mountain with the **matching** number 
               
               <span style="background-color: yellow">KJB</span>: Instead of saying 
               the output is just a number, call it the index of the mountain to 
               shoot. Using programming terminology helps your fellow programmers
               understand the code.

            */

            printf("%d\n", currentMountain);
    
    /* **Rough Sketch of Solution** */
    // ![Image](SketchHowISolved.jpg)
    
    } 
    /* end of while */
    
    return 0;
}
/* end of main */
