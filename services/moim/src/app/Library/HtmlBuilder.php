<?php


namespace App\Library;


use Illuminate\Support\HtmlString;

class HtmlBuilder
{
    protected function attributeElement($key, $value)
    {
        if (is_numeric($key)) {
            return $value;
        }

        // Treat boolean attributes as HTML properties
        if (is_bool($value) && $key !== 'value') {
            return $value ? $key : '';
        }

        if (is_array($value) && $key === 'class') {
            return 'class="' . implode(' ', $value) . '"';
        }

        if (!is_null($value)) {
            return $key . '="' . e($value, false) . '"';
        }
        return $value;
    }

    public function attributes($attributes)
    {
        $html = [];

        foreach ((array)$attributes as $key => $value) {
            $element = $this->attributeElement($key, $value);

            if (!is_null($element)) {
                $html[] = $element;
            }
        }

        return count($html) > 0 ? ' ' . implode(' ', $html) : '';
    }

    public function image($url, $alt = null, $attributes = [], $secure = null)
    {
        $attributes['alt'] = $alt;

        return $this->toHtmlString('<img src="' . e($url) . '"' . $this->attributes($attributes) . '>');
    }

    public function text($text) {
        return $this->toHTMLString(e($text));
    }

    public function toHTMLString($html)
    {
        return new HtmlString($html);
    }
}
