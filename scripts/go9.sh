#!/bin/bash
declare -A GO9_tt #target table

. nenv $* # SETS some useful environment variables

GO9_padding="                                                                    "

#GO9_tt[]=""
go9() {
    answer=$(go9.py $*)
    eval $answer
}

go()
{
    answer=$(go9.py go $*)
    eval $answer
}
