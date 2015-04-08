# add the dev directory to the path and pythonpath
if ( ${?_PYF_ACTIVATED} ) then
    echo 'Already activated'
else
    set pwd=`pwd`
    setenv _PATH_BEFORE_PYF_ACTIVATE $PATH
    setenv PATH $pwd/dev:$PATH

    if ( ${?PYTHONPATH} ) then
        setenv _PYTHONPATH_BEFORE_PYF_ACTIVATE $PYTHONPATH
        setenv PYTHONPATH $pwd/dev:$PYTHONPATH
    else
        setenv _PYTHONPATH_BEFORE_PYF_ACTIVATE
        setenv PYTHONPATH $pwd/dev
    endif

    setenv _PYF_ACTIVATED
endif
