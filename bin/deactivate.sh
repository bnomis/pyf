if [ $_PYF_ACTIVATED ]; then
    
    if [ $_PATH_BEFORE_PYF_ACTIVATE ]; then
        export PATH=$_PATH_BEFORE_PYF_ACTIVATE
    fi

    if [ $_PYTHONPATH_BEFORE_PYF_ACTIVATE ]; then
        if [  $_PYTHONPATH_BEFORE_PYF_ACTIVATE != 0 ]; then
            export PYTHONPATH=$_PYTHONPATH_BEFORE_PYF_ACTIVATE
        else
            unset PYTHONPATH
        fi
    fi

    unset _PATH_BEFORE_PYF_ACTIVATE
    unset _PYTHONPATH_BEFORE_PYF_ACTIVATE
    unset _PYF_ACTIVATED
else
    echo 'Not active'
fi
    