if ( ${?_PYF_ACTIVATED} ) then
    
    if ( ${?_PATH_BEFORE_PYF_ACTIVATE} ) then
        setenv PATH $_PATH_BEFORE_PYF_ACTIVATE
    endif

    if ( ${?_PYTHONPATH_BEFORE_PYF_ACTIVATE} ) then
        if ( { eval 'test ! -z $_PYTHONPATH_BEFORE_PYF_ACTIVATE' } ) then
            setenv PYTHONPATH $_PYTHONPATH_BEFORE_PYF_ACTIVATE
        else
            unsetenv PYTHONPATH
        endif
    endif

    unsetenv _PATH_BEFORE_PYF_ACTIVATE
    unsetenv _PYTHONPATH_BEFORE_PYF_ACTIVATE
    unsetenv _PYF_ACTIVATED
else
    echo 'Not active'
endif
    